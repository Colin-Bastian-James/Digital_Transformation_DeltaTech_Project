"""Emergency red-flag rules, checked BEFORE the model.

The list lives in prompts/red_flags.json (one entry per emergency sign, with
regular expressions in English and French, and the sources). To add a rule,
add a pattern there: no code change needed.

check_red_flags(text) returns the first matching flag as
    {"id": "chest_pain", "reason": "...", "matched": "chest pain"}
or None if no red flag is found.
"""
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RED_FLAGS_FILE = ROOT / "prompts" / "red_flags.json"

# A negation just before a match cancels it: "no chest pain", "pas de douleur thoracique".
NEGATION = re.compile(
    r"\b(no|not|never|without|denies|pas|sans|aucune?|jamais|ni)\b(\W+\w+){0,2}\W*$")


def normalise(text: str) -> str:
    """Lower case, remove accents, unify apostrophes, so 'Thoracique' == 'thoracique'."""
    text = text.lower().replace("’", "'")
    text = unicodedata.normalize("NFKD", text)
    return "".join(c for c in text if not unicodedata.combining(c))


def load_flags() -> list:
    flags = json.loads(RED_FLAGS_FILE.read_text(encoding="utf-8"))["flags"]
    for flag in flags:
        flag["compiled"] = [re.compile(p) for p in flag["patterns"]]
    return flags


FLAGS = load_flags()


def is_negated(text: str, start: int) -> bool:
    """True if a negation word appears in the same sentence, at most 3 words before the match."""
    before = re.split(r"[.!?;\n]|\bbut\b|\bmais\b", text[:start])[-1]
    return bool(NEGATION.search(before))


def check_red_flags(symptoms: str):
    text = normalise(symptoms)
    for flag in FLAGS:
        for pattern in flag["compiled"]:
            for match in pattern.finditer(text):
                if not is_negated(text, match.start()):
                    return {"id": flag["id"], "reason": flag["reason"],
                            "matched": match.group(0)}
    return None
