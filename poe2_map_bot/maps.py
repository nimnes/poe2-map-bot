from __future__ import annotations

import json
from dataclasses import dataclass
from difflib import SequenceMatcher, get_close_matches
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class MapProfile:
    name: str
    aliases: tuple[str, ...]
    summary: str
    biome: str
    base_tileset: str
    boss: str
    notes: str
    hc_difficulty: str
    risk_score: int
    threats: tuple[str, ...]
    tips: tuple[str, ...]
    tags: tuple[str, ...]
    source_url: str

    @classmethod
    def from_dict(cls, value: dict) -> "MapProfile":
        return cls(
            name=str(value["name"]).strip(),
            aliases=tuple(str(item).strip() for item in value.get("aliases", []) if str(item).strip()),
            summary=str(value.get("summary", "")).strip(),
            biome=str(value.get("biome", "")).strip(),
            base_tileset=str(value.get("base_tileset", "")).strip(),
            boss=str(value.get("boss", "")).strip(),
            notes=str(value.get("notes", "")).strip(),
            hc_difficulty=str(value.get("hc_difficulty", "Unrated")).strip(),
            risk_score=int(value.get("risk_score", 3)),
            threats=tuple(str(item).strip() for item in value.get("threats", []) if str(item).strip()),
            tips=tuple(str(item).strip() for item in value.get("tips", []) if str(item).strip()),
            tags=tuple(str(item).strip() for item in value.get("tags", []) if str(item).strip()),
            source_url=str(value.get("source_url", "")).strip(),
        )

    @property
    def search_terms(self) -> tuple[str, ...]:
        return (self.name, *self.aliases)


class MapBook:
    def __init__(self, profiles: Iterable[MapProfile]):
        self._profiles = sorted(profiles, key=lambda item: item.name.casefold())
        self._term_to_profile: dict[str, MapProfile] = {}
        for profile in self._profiles:
            for term in profile.search_terms:
                self._term_to_profile[normalize(term)] = profile

    @classmethod
    def load(cls, path: Path) -> "MapBook":
        with path.open("r", encoding="utf-8") as handle:
            raw = json.load(handle)
        return cls(MapProfile.from_dict(item) for item in raw["maps"])

    @property
    def profiles(self) -> tuple[MapProfile, ...]:
        return tuple(self._profiles)

    def find(self, query: str) -> tuple[MapProfile | None, list[str]]:
        normalized = normalize(query)
        if not normalized:
            return None, []

        exact = self._term_to_profile.get(normalized)
        if exact:
            return exact, []

        contains = [
            profile
            for profile in self._profiles
            if any(normalized in normalize(term) for term in profile.search_terms)
        ]
        if len(contains) == 1:
            return contains[0], []

        terms = list(self._term_to_profile.keys())
        close_terms = get_close_matches(normalized, terms, n=5, cutoff=0.55)
        suggestions = unique(profile.name for term in close_terms if (profile := self._term_to_profile.get(term)))

        if not suggestions:
            ranked = sorted(
                self._profiles,
                key=lambda profile: max(similarity(normalized, normalize(term)) for term in profile.search_terms),
                reverse=True,
            )
            suggestions = [profile.name for profile in ranked[:5]]

        if suggestions:
            best = self._term_to_profile.get(normalize(suggestions[0]))
            best_score = similarity(normalized, normalize(suggestions[0]))
            if best and best_score >= 0.82:
                return best, suggestions[1:]

        return None, suggestions


def normalize(value: str) -> str:
    return " ".join(value.casefold().replace("-", " ").replace("_", " ").split())


def similarity(left: str, right: str) -> float:
    return SequenceMatcher(None, left, right).ratio()


def unique(values: Iterable[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        key = normalize(value)
        if key in seen:
            continue
        seen.add(key)
        result.append(value)
    return result


def difficulty_meter(risk_score: int, maximum: int = 5) -> str:
    score = max(0, min(risk_score, maximum))
    return "★" * score + "☆" * (maximum - score)


def format_profile(profile: MapProfile) -> str:
    facts = []
    if profile.biome:
        facts.append(f"Biome: {profile.biome}")
    if profile.base_tileset:
        facts.append(f"Tileset: {profile.base_tileset}")
    if profile.boss:
        facts.append(f"Boss: {profile.boss}")
    if profile.tags:
        facts.append(f"Tags: {', '.join(profile.tags)}")

    facts_text = "\n".join(f"- {item}" for item in facts)
    notes_text = profile.notes or "No extra wiki notes recorded."
    threats = "\n".join(f"- {item}" for item in profile.threats) or "- No specific threats recorded yet."
    tips = "\n".join(f"- {item}" for item in profile.tips) or "- Treat unknown rares and boss phases cautiously."
    details = f"\n\n*Map facts*\n{escape_md(facts_text)}" if facts_text else ""
    difficulty_line = (
        f"HC difficulty: *{escape_md(profile.hc_difficulty)}*\n"
        f"Risk: {difficulty_meter(profile.risk_score)} \\({profile.risk_score}/5\\)"
    )
    return (
        f"*{escape_md(profile.name)}*\n"
        f"{difficulty_line}\n\n"
        f"{escape_md(profile.summary or 'No detailed summary recorded yet.')}"
        f"{details}\n\n"
        f"*Wiki notes*\n{escape_md(notes_text)}\n\n"
        f"*Main threats*\n{escape_md(threats)}\n\n"
        f"*HC tips*\n{escape_md(tips)}"
    )


def escape_md(value: str) -> str:
    special = r"_*[]()~`>#+-=|{}.!"
    return "".join(f"\\{char}" if char in special else char for char in value)
