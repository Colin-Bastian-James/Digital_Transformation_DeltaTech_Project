"""DeltaTech Triage Assistant: backend (MVP).

get_triage(symptoms) returns a recommendation as a dict:
    {"appointment_type": "GP", "urgency": "same-day",
     "confidence": "medium", "reason": "one short sentence",
     "source": "red_flag" | "model" | "fallback"}

Order of the checks (safety first):
1. Red-flag rules (app/red_flags.py, list in prompts/red_flags.json).
   A red flag ALWAYS returns EMERGENCY / call 112; the model is not asked.
2. Otherwise the local llama3.2 model in Ollama, with prompts/triage.txt.
3. The model's answer must be one of a fixed set of outcomes. Anything else,
   an unreadable answer, or no answer within TIMEOUT_S gives the safe default:
   "contact your GP today; if it gets worse, call 112".

Every triage is written to logs/triage_log.jsonl (input, output, source,
model and rule versions) so a hospital can audit it. logs/ is git-ignored
because it contains health data.

Settings come from environment variables (see .env.example):
    OLLAMA_URL    default http://localhost:11434
    OLLAMA_MODEL  default llama3.2
Patient text is only sent to this local Ollama server, never to a third party.
Standard library only, like the M2 experiment.
"""
import hashlib
import json
import os
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from red_flags import RED_FLAGS_FILE, check_red_flags

ROOT = Path(__file__).resolve().parent.parent
PROMPT_FILE = ROOT / "prompts" / "triage.txt"
LOG_FILE = ROOT / "logs" / "triage_log.jsonl"

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2")
TIMEOUT_S = 20  # median answer is ~7 s (M2); after 20 s we give the safe default

APPOINTMENT_TYPES = {"EMERGENCY", "OUT_OF_HOURS_GP", "GP", "SPECIALIST",
                     "SELF_CARE", "NEEDS_MORE_INFO"}
URGENCIES = {"emergency", "same-day", "routine"}
CONFIDENCES = {"high", "medium", "low"}


def file_version(path: Path) -> str:
    """Short fingerprint of a file: changes whenever the file's content changes."""
    return hashlib.sha256(path.read_bytes()).hexdigest()[:8]


def load_prompt() -> str:
    """Read the system prompt from prompts/triage.txt."""
    return PROMPT_FILE.read_text(encoding="utf-8")


def ask_ollama(symptoms: str) -> str:
    """Send one patient message to Ollama and return the model's raw text answer."""
    payload = {
        "model": OLLAMA_MODEL,
        "stream": False,
        "format": "json",               # forces the model to answer in JSON
        "options": {"temperature": 0},  # same answer for the same input
        "messages": [
            {"role": "system", "content": load_prompt()},
            {"role": "user", "content": symptoms},
        ],
    }
    req = urllib.request.Request(
        f"{OLLAMA_URL}/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=TIMEOUT_S) as resp:
        return json.loads(resp.read())["message"]["content"]


def safe_default(reason: str) -> dict:
    """Used whenever we cannot trust the model's answer."""
    return {"appointment_type": "GP", "urgency": "same-day", "confidence": "low",
            "reason": reason + " Please contact your GP today. If it gets worse, call 112.",
            "source": "fallback"}


def parse_answer(raw: str) -> dict:
    """Accept the model's answer only if it is one of the fixed outcomes."""
    try:
        answer = json.loads(raw)
    except json.JSONDecodeError:
        return safe_default("We could not read the assistant's answer.")
    if not isinstance(answer, dict):
        return safe_default("We could not read the assistant's answer.")

    appointment = str(answer.get("appointment_type", "")).strip().upper()
    urgency = str(answer.get("urgency", "")).strip().lower()
    confidence = str(answer.get("confidence", "")).strip().lower()
    reason = str(answer.get("reason", "")).strip()

    if appointment not in APPOINTMENT_TYPES:
        return safe_default("The assistant gave an answer we do not support.")
    if urgency not in URGENCIES:
        # Safe default: an emergency is always "now", anything else "today".
        urgency = "emergency" if appointment == "EMERGENCY" else "same-day"
    if confidence not in CONFIDENCES:
        confidence = "low"
    return {"appointment_type": appointment, "urgency": urgency,
            "confidence": confidence, "reason": reason or "No explanation given.",
            "source": "model"}


def log_triage(symptoms: str, result: dict, detail: str = "") -> None:
    """Append one line per triage to logs/triage_log.jsonl for auditing."""
    entry = {
        "time": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "input": symptoms,
        "output": result,
        "detail": detail,
        "model": OLLAMA_MODEL,
        "prompt_version": file_version(PROMPT_FILE),
        "red_flags_version": file_version(RED_FLAGS_FILE),
    }
    try:
        LOG_FILE.parent.mkdir(exist_ok=True)
        with LOG_FILE.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
    except OSError:
        pass  # logging must never block a triage


def get_triage(symptoms: str) -> dict:
    """Main entry point used by app.py."""
    # 1. Red flags first: the model can never downgrade an emergency sign.
    flag = check_red_flags(symptoms)
    if flag:
        result = {"appointment_type": "EMERGENCY", "urgency": "emergency",
                  "confidence": "high", "reason": flag["reason"], "source": "red_flag"}
        log_triage(symptoms, result, f"red flag {flag['id']}: '{flag['matched']}'")
        return result

    # 2. The local model, with a time limit.
    try:
        raw = ask_ollama(symptoms)
    except (urllib.error.URLError, TimeoutError, OSError) as err:
        result = safe_default("The assistant did not answer in time.")
        log_triage(symptoms, result, f"ollama error: {err}")
        return result

    # 3. Only the fixed set of outcomes is accepted.
    result = parse_answer(raw)
    log_triage(symptoms, result, "raw model answer: " + raw[:300])
    return result


if __name__ == "__main__":
    # Quick manual test:  python app/triage.py "I twisted my ankle, it is swollen"
    import sys
    text = " ".join(sys.argv[1:]) or "I twisted my ankle yesterday, it is swollen and I can barely walk."
    print(json.dumps(get_triage(text), indent=2))
