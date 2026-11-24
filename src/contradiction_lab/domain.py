"""Domain vocabulary lives with the corpus data, not in pipeline code."""

import json
import re
from functools import lru_cache
from importlib.resources import files


@lru_cache
def load_domain() -> dict:
    raw = json.loads(
        files("contradiction_lab").joinpath("data/corpus.json").read_text(encoding="utf-8")
    )
    return raw.get("domain", {})


def _pattern(needle: str) -> str:
    # Needles are word-initial stems ("hypertroph"); short abbreviations ("mt")
    # must also end at a word boundary so "mtor" does not match.
    tail = r"(?![a-z])" if len(needle) <= 3 and needle.isalpha() else ""
    return r"(?<![a-z])" + re.escape(needle) + tail


def canonical(value: str | None, keywords: dict[str, list[str]]) -> str | None:
    """Map free-text model output onto a canonical label by first keyword match."""
    if not value:
        return value
    text = value.strip().casefold()
    for label, needles in keywords.items():
        if text == label or any(re.search(_pattern(needle), text) for needle in needles):
            return label
    return text
