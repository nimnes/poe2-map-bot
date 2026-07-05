# PoE 2 HC Map Telegram Bot

A small Telegram bot that answers Path of Exile 2 map and boss queries with a summary, a hardcore risk rating, and practical tips.

## Features

- `/map <name>` returns the best matching map profile.
- `/boss <name>` returns the best matching boss guide.
- Plain messages such as `Augury` also work.
- `/maps` lists known maps.
- `/bosses` lists known bosses.
- `/reload` reloads `data/maps.json` and `data/bosses.json` without restarting the bot.
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

Optional data path overrides:

```bash
MAP_DATA_PATH=data/maps.json
BOSS_DATA_PATH=data/bosses.json
```

Create a bot token with Telegram's BotFather, then run:

```bash
python -m poe2_map_bot.bot
```

For hosting and Telegram registration, see [DEPLOYMENT.md](DEPLOYMENT.md).

## Refreshing Map Names

The bot works from `data/maps.json`. To merge in map names from the wiki:

```bash
python scripts/update_maps_from_wiki.py
```

The updater preserves your existing summaries, difficulty ratings, and tips. New maps are added with starter HC notes so you can curate them later.

## Data Format

The bot loads map data from `data/maps.json` and boss data from `data/bosses.json`.

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

Each boss entry includes access notes, HC risk notes, and optional source/video links:

```json
{
  "name": "The Arbiter of Ash",
  "aliases": ["Arbiter", "Arbiter of Ash", "Burning Monolith"],
  "category": "Pinnacle",
  "access": "Burning Monolith after collecting Crisis Fragments.",
  "summary": "Primary endgame pinnacle boss with multi-phase arena pressure.",
  "hc_difficulty": "Extreme",
  "risk_score": 5,
  "threats": ["Arena-wide patterns", "Expensive failed learning pulls"],
  "tips": ["Do not make the first HC attempt blind.", "Prioritize survival over uptime."],
  "source_url": "https://www.pcgamer.com/games/rpg/path-of-exile-2-dawn-of-the-hunt-endgame/",
  "video_url": "https://www.youtube.com/watch?v=TMYtjqhk3nA"
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
