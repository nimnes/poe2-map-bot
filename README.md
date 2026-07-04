# PoE 2 HC Map Telegram Bot

A small Telegram bot that answers map-name queries with a Path of Exile 2 map summary, a hardcore risk rating, and practical tips.

## Features

- `/map <name>` returns the best matching map profile.
- Plain messages such as `Augury` also work.
- `/maps` lists known maps.
- `/reload` reloads `data/maps.json` without restarting the bot.
- Fuzzy matching helps with partial names and typos.
- `scripts/update_maps_from_wiki.py` can refresh map names from the Fextralife maps page.

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env` and set your Telegram bot token:

```bash
TELEGRAM_BOT_TOKEN=123456:your-token
```

Create a bot token with Telegram's BotFather, then run:

```bash
python -m poe2_map_bot.bot
```

## Refreshing Map Names

The bot works from `data/maps.json`. To merge in map names from the wiki:

```bash
python scripts/update_maps_from_wiki.py
```

The updater preserves your existing summaries, difficulty ratings, and tips. New maps are added with starter HC notes so you can curate them later.

## Data Format

Each map entry includes wiki table facts plus HC notes:

```json
{
  "name": "Augury",
  "aliases": ["augury map"],
  "biome": "Grass, Forest, Swamp",
  "base_tileset": "Jiquani's Machinarium",
  "boss": "Gressor-Kul, the Apex",
  "notes": "Features three Stone Altars...",
  "summary": "Short map description.",
  "hc_difficulty": "High",
  "risk_score": 4,
  "threats": ["Tight paths", "Boss burst windows"],
  "tips": ["Scout corners before committing.", "Skip damage mods if your recovery is weak."],
  "tags": ["constrained"],
  "source_url": "https://pathofexile2.wiki.fextralife.com/Maps"
}
```

The current bundled database contains 116 maps parsed from the wiki table. The wiki data supplies map name, biome, base tileset, boss, and notes. HC difficulty, threats, and tips are curated/derived from those fields and should be reviewed as the game balance changes.

`risk_score` is 1-5:

- `1`: Very comfortable for HC.
- `2`: Manageable with normal caution.
- `3`: Respect damage/map mods.
- `4`: Dangerous for undergeared HC characters.
- `5`: Avoid unless you know the encounter and build matchup.

## Notes

Fextralife pages can change structure or block automated requests. If the updater cannot parse the page, save the wiki page HTML manually and run:

```bash
python scripts/update_maps_from_wiki.py --html path/to/maps.html
```
