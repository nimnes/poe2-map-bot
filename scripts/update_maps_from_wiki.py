from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup


DEFAULT_URL = "https://pathofexile2.wiki.fextralife.com/Maps"
DEFAULT_DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "maps.json"
STARTER_SUMMARY = "A Path of Exile 2 endgame map imported from the wiki map list. This entry needs curated layout, boss, and HC notes."


def main() -> None:
    parser = argparse.ArgumentParser(description="Merge map names from the Fextralife PoE 2 maps page.")
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--html", type=Path, help="Read a saved wiki HTML file instead of fetching the URL.")
    parser.add_argument("--data", type=Path, default=DEFAULT_DATA_PATH)
    args = parser.parse_args()

    html = args.html.read_text(encoding="utf-8") if args.html else fetch(args.url)
    scraped = scrape_maps(html, args.url)
    if not scraped:
        raise SystemExit("No map names found. The wiki layout may have changed.")

    existing = load_data(args.data)
    merged = merge_maps(existing, scraped)
    args.data.write_text(json.dumps(merged, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Merged {len(scraped)} wiki maps into {args.data}")


def fetch(url: str) -> str:
    response = requests.get(
        url,
        timeout=30,
        headers={"User-Agent": "poe2-hc-map-bot/1.0 (+personal Telegram bot map index)"},
    )
    response.raise_for_status()
    return response.text


def scrape_maps(html: str, base_url: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    table_rows = scrape_map_table(soup, base_url)
    if table_rows:
        return table_rows

    candidates: dict[str, dict] = {}

    for table in soup.select("table"):
        header_text = " ".join(th.get_text(" ", strip=True).casefold() for th in table.select("th"))
        if "map" not in header_text and "area" not in header_text:
            continue
        for link in table.select("a[href]"):
            add_candidate(candidates, link.get_text(" ", strip=True), link["href"], base_url)

    for link in soup.select("a[href]"):
        href = link.get("href", "")
        text = link.get_text(" ", strip=True)
        if looks_like_map_link(text, href):
            add_candidate(candidates, text, href, base_url)

    return sorted(candidates.values(), key=lambda item: item["name"].casefold())


def scrape_map_table(soup: BeautifulSoup, base_url: str) -> list[dict]:
    for table in soup.select("table"):
        rows = table.select("tr")
        if not rows:
            continue
        headers = [cell.get_text(" ", strip=True) for cell in rows[0].select("th,td")]
        if headers[:5] != ["Map Name", "Biome", "Base Tileset", "Boss", "Notes"]:
            continue

        maps = []
        for row in rows[1:]:
            cells = [clean_cell(cell.get_text(" ", strip=True)) for cell in row.select("th,td")]
            if len(cells) < 5 or not cells[0]:
                continue
            name, biome, base_tileset, boss, notes = cells[:5]
            maps.append(
                {
                    "name": name,
                    "aliases": aliases_for(name),
                    "biome": biome,
                    "base_tileset": base_tileset,
                    "boss": boss,
                    "notes": notes,
                    "wiki_url": base_url,
                }
            )
        return sorted(maps, key=lambda item: item["name"].casefold())
    return []


def add_candidate(candidates: dict[str, dict], text: str, href: str, base_url: str) -> None:
    name = clean_name(text)
    if not name or name.casefold() in {"maps", "map", "waystone"}:
        return
    key = name.casefold()
    candidates[key] = {"name": name, "wiki_url": urljoin(base_url, href)}


def looks_like_map_link(text: str, href: str) -> bool:
    if not text or len(text) > 60:
        return False
    if re.search(r"\b(map|waystone)\b", text, flags=re.I):
        return True
    return "/Maps/" in href or href.endswith("+Map")


def clean_name(value: str) -> str:
    value = re.sub(r"\s+", " ", value).strip()
    value = re.sub(r"\s+Map$", "", value, flags=re.I)
    return value


def clean_cell(value: str) -> str:
    value = re.sub(r"\s+", " ", value).strip()
    return "" if value in {"—", "-"} else value


def aliases_for(name: str) -> list[str]:
    aliases = [f"{name} map"]
    if name.startswith("The "):
        aliases.append(name[4:])
    return aliases


def load_data(path: Path) -> dict:
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {"source": DEFAULT_URL, "maps": []}


def merge_maps(existing: dict, scraped: list[dict]) -> dict:
    by_name = {item["name"].casefold(): item for item in existing.get("maps", [])}
    for item in scraped:
        key = item["name"].casefold()
        if key in by_name:
            by_name[key]["source_url"] = item.get("wiki_url")
            for field in ("aliases", "biome", "base_tileset", "boss", "notes"):
                if item.get(field) is not None:
                    by_name[key][field] = item[field]
            continue
        by_name[key] = {
            "name": item["name"],
            "aliases": item.get("aliases") or aliases_for(item["name"]),
            "biome": item.get("biome", ""),
            "base_tileset": item.get("base_tileset", ""),
            "boss": item.get("boss", ""),
            "notes": item.get("notes", ""),
            "summary": starter_summary(item),
            "hc_difficulty": "Unrated",
            "risk_score": 3,
            "threats": ["Threats have not been curated yet."],
            "tips": [
                "Run conservative mods while the entry is unrated.",
                "Learn the boss before adding damage, speed, or extra projectiles.",
                "Skip unknown rare-mod combinations on important HC characters."
            ],
            "tags": [],
            "source_url": item.get("wiki_url")
        }
    existing["maps"] = sorted(by_name.values(), key=lambda item: item["name"].casefold())
    return existing


def starter_summary(item: dict) -> str:
    name = item["name"]
    biome = item.get("biome", "")
    boss = item.get("boss", "")
    if boss:
        return f"{name} is a {biome or 'Path of Exile 2'} map with listed boss {boss}. This entry needs curated HC notes."
    return STARTER_SUMMARY


if __name__ == "__main__":
    main()
