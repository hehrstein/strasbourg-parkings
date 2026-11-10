"""Tests for runtime translation files."""

from __future__ import annotations

import json
from pathlib import Path


def test_english_runtime_translation_matches_default_strings() -> None:
    """English must exist because Home Assistant uses it as a fallback."""
    integration = Path(__file__).parents[1] / "custom_components" / "strasbourg_parkings"
    translations = integration / "translations"

    strings = json.loads((integration / "strings.json").read_text("utf-8"))
    english = json.loads((translations / "en.json").read_text("utf-8"))
    french = json.loads((translations / "fr.json").read_text("utf-8"))

    assert english == strings
    assert english["config"]["step"].keys() == french["config"]["step"].keys()
    assert english["options"]["step"].keys() == french["options"]["step"].keys()
