from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from poe2_map_bot.maps import difficulty_meter, escape_md, normalize, similarity, unique


@dataclass(frozen=True)
class BossGuide:
    name: str
    aliases: tuple[str, ...]
    category: str
    access: str
    summary: str
    hc_difficulty: str
    risk_score: int
    threats: tuple[str, ...]
    tips: tuple[str, ...]
    source_url: str
    video_url: str

    @classmethod
    def from_dict(cls, value: dict) -> "BossGuide":
        return cls(
            name=str(value["name"]).strip(),
            aliases=tuple(str(item).strip() for item in value.get("aliases", []) if str(item).strip()),
            category=str(value.get("category", "")).strip(),
            access=str(value.get("access", "")).strip(),
            summary=str(value.get("summary", "")).strip(),
            hc_difficulty=str(value.get("hc_difficulty", "Unrated")).strip(),
            risk_score=int(value.get("risk_score", 3)),
            threats=tuple(str(item).strip() for item in value.get("threats", []) if str(item).strip()),
            tips=tuple(str(item).strip() for item in value.get("tips", []) if str(item).strip()),
            source_url=str(value.get("source_url", "")).strip(),
            video_url=str(value.get("video_url", "")).strip(),
        )

    @property
    def search_terms(self) -> tuple[str, ...]:
        return (self.name, *self.aliases)


class BossBook:
    def __init__(self, guides: Iterable[BossGuide]):
        self._guides = sorted(guides, key=lambda item: item.name.casefold())
        self._term_to_guide: dict[str, BossGuide] = {}
        for guide in self._guides:
            for term in guide.search_terms:
                self._term_to_guide[normalize(term)] = guide

    @classmethod
    def load(cls, path: Path) -> "BossBook":
        with path.open("r", encoding="utf-8") as handle:
            raw = json.load(handle)
        return cls(BossGuide.from_dict(item) for item in raw["bosses"])

    @property
    def guides(self) -> tuple[BossGuide, ...]:
        return tuple(self._guides)

    def find(self, query: str) -> tuple[BossGuide | None, list[str]]:
        normalized = normalize(query)
        if not normalized:
            return None, []

        exact = self._term_to_guide.get(normalized)
        if exact:
            return exact, []

        contains = [
            guide
            for guide in self._guides
            if any(normalized in normalize(term) for term in guide.search_terms)
        ]
        if len(contains) == 1:
            return contains[0], []

        ranked = sorted(
            self._guides,
            key=lambda guide: max(similarity(normalized, normalize(term)) for term in guide.search_terms),
            reverse=True,
        )
        suggestions = unique(guide.name for guide in ranked[:5])
        if suggestions:
            best = self._term_to_guide.get(normalize(suggestions[0]))
            if best and similarity(normalized, normalize(suggestions[0])) >= 0.82:
                return best, suggestions[1:]
        return None, suggestions


def format_boss_guide(guide: BossGuide) -> str:
    facts = []
    if guide.category:
        facts.append(f"Type: {guide.category}")
    if guide.access:
        facts.append(f"Access: {guide.access}")

    facts_text = "\n".join(f"- {item}" for item in facts)
    threats = "\n".join(f"- {item}" for item in guide.threats) or "- No specific threats recorded yet."
    tips = "\n".join(f"- {item}" for item in guide.tips) or "- Scout on a lower-risk character before committing HC."
    video = f"\n\n*Video guide search*\n{escape_md(guide.video_url)}" if guide.video_url else ""
    source = f"\n\n*Source*\n{escape_md(guide.source_url)}" if guide.source_url else ""
    return (
        f"*{escape_md(guide.name)}*\n"
        f"HC difficulty: *{escape_md(guide.hc_difficulty)}*\n"
        f"Risk: {difficulty_meter(guide.risk_score)} \\({guide.risk_score}/5\\)\n\n"
        f"{escape_md(guide.summary or 'No detailed guide recorded yet.')}\n\n"
        f"*Boss facts*\n{escape_md(facts_text)}\n\n"
        f"*Main threats*\n{escape_md(threats)}\n\n"
        f"*HC tips*\n{escape_md(tips)}"
        f"{video}"
        f"{source}"
    )


def format_boss_list(guides: Iterable[BossGuide]) -> str:
    names = ", ".join(guide.name for guide in guides)
    return escape_md(f"Known boss guides:\n{names}")
