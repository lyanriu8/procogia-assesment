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


def canonical(value: str | None, keywords: dict[str, list[str]]) -> str | None:
    """Map free-text model output onto a canonical label by first keyword match."""
    if not value:
        return value
    text = value.strip().casefold()
    for label, needles in keywords.items():
        if text == label or any(
            re.search(r"(?<![a-z])" + re.escape(needle), text) for needle in needles
        ):
            return label
    return text
