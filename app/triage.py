"""DeltaTech Triage Assistant: backend (MVP).

get_triage(symptoms) sends the patient's message to the local llama3.2 model
running in Ollama and returns a recommendation as a dict:
    {"appointment_type": "GP", "urgency": "same-day",
     "confidence": "medium", "reason": "one short sentence"}

The prompt lives in prompts/triage.txt (versioned with the code).
Settings come from environment variables (see .env.example):
    OLLAMA_URL    default http://localhost:11434
    OLLAMA_MODEL  default llama3.2
Patient text is only sent to this local Ollama server, never to a third party.
Standard library only, like the M2 experiment.
"""
import json
import os
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROMPT_FILE = ROOT / "prompts" / "triage.txt"

OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2")
TIMEOUT_S = 60

APPOINTMENT_TYPES = {"EMERGENCY", "OUT_OF_HOURS_GP", "GP", "SPECIALIST",
                     "SELF_CARE", "NEEDS_MORE_INFO"}
URGENCIES = {"emergency", "same-day", "routine"}
CONFIDENCES = {"high", "medium", "low"}


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


def parse_answer(raw: str) -> dict:
    """Turn the model's text into a clean result; anything invalid becomes NEEDS_MORE_INFO."""
    try:
        answer = json.loads(raw)
    except json.JSONDecodeError:
        return fallback("We could not read the assistant's answer. Please rephrase your symptoms.")
    if not isinstance(answer, dict):
        return fallback("We could not read the assistant's answer. Please rephrase your symptoms.")

    appointment = str(answer.get("appointment_type", "")).strip().upper()
    urgency = str(answer.get("urgency", "")).strip().lower()
    confidence = str(answer.get("confidence", "")).strip().lower()
    reason = str(answer.get("reason", "")).strip()

    if appointment not in APPOINTMENT_TYPES:
        return fallback("The assistant was not sure. Please add more detail about your symptoms.")
    if urgency not in URGENCIES:
        # Safe default: an emergency is always "now", anything else "today".
        urgency = "emergency" if appointment == "EMERGENCY" else "same-day"
    if confidence not in CONFIDENCES:
        confidence = "low"
    return {"appointment_type": appointment, "urgency": urgency,
            "confidence": confidence, "reason": reason or "No explanation given."}


def fallback(reason: str) -> dict:
    return {"appointment_type": "NEEDS_MORE_INFO", "urgency": "routine",
            "confidence": "low", "reason": reason}


def get_triage(symptoms: str) -> dict:
    """Main entry point used by app.py.

    TODO (by 02 Nov): run the red-flag rules here BEFORE calling the model,
    so a red flag always returns EMERGENCY and the model cannot downgrade it.
    """
    try:
        raw = ask_ollama(symptoms)
    except (urllib.error.URLError, TimeoutError, OSError):
        return fallback("The triage service is not available right now. "
                        "If you feel very unwell, call 112.")
    return parse_answer(raw)


if __name__ == "__main__":
    # Quick manual test:  python app/triage.py "I twisted my ankle, it is swollen"
    import sys
    text = " ".join(sys.argv[1:]) or "I twisted my ankle yesterday, it is swollen and I can barely walk."
    print(json.dumps(get_triage(text), indent=2))
