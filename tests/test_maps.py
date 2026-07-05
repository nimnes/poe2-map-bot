from poe2_map_bot.maps import MapBook, MapProfile, difficulty_meter, format_profile, normalize


def book() -> MapBook:
    return MapBook(
        [
            MapProfile(
                name="Augury",
                aliases=("augury map",),
                summary="summary",
                biome="Grass",
                base_tileset="Jiquani's Machinarium",
                boss="Gressor-Kul, the Apex",
                notes="notes",
                hc_difficulty="High",
                risk_score=4,
                threats=("threat",),
                tips=("tip",),
                tags=("constrained",),
                source_url="https://pathofexile2.wiki.fextralife.com/Maps",
            ),
            MapProfile(
                name="Crypt",
                aliases=("crypt map",),
                summary="summary",
                biome="Desert, Grass",
                base_tileset="",
                boss="Meltwax, Mockery of Faith",
                notes="notes",
                hc_difficulty="Medium",
                risk_score=3,
                threats=("threat",),
                tips=("tip",),
                tags=(),
                source_url="https://pathofexile2.wiki.fextralife.com/Maps",
            ),
        ]
    )


def test_normalize_handles_case_and_separators():
    assert normalize("  Augury_Map ") == "augury map"


def test_exact_alias_lookup():
    profile, suggestions = book().find("augury map")
    assert profile is not None
    assert profile.name == "Augury"
    assert suggestions == []


def test_fuzzy_lookup():
    profile, _ = book().find("agury")
    assert profile is not None
    assert profile.name == "Augury"


def test_unknown_returns_suggestions():
    profile, suggestions = book().find("crp")
    assert profile is None
    assert "Crypt" in suggestions


def test_difficulty_meter_clamps_score():
    assert difficulty_meter(4) == "★★★★☆"
    assert difficulty_meter(7) == "★★★★★"
    assert difficulty_meter(-1) == "☆☆☆☆☆"


def test_format_profile_includes_star_risk_line():
    profile = book().profiles[0]

    message = format_profile(profile)

    assert "Risk: ★★★★☆ \\(4/5\\)" in message
