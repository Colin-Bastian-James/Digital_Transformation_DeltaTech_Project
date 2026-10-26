"""DeltaTech Triage Assistant: web interface (MVP).

Run from the repository root:
    python app/app.py
then open http://localhost:5000
"""
from flask import Flask, render_template, request

app = Flask(__name__)

LABELS = {
    "EMERGENCY": "Emergency department, now",
    "OUT_OF_HOURS_GP": "On-call GP (maison médicale de garde)",
    "GP": "General practitioner",
    "SPECIALIST": "Specialist (with your referral)",
    "SELF_CARE": "Pharmacy and self-care, no appointment needed",
    "NEEDS_MORE_INFO": "Please add more detail",
}

URGENCY = {
    "emergency": "Now",
    "same-day": "Today",
    "routine": "In the next days",
}


def get_triage(symptoms: str) -> dict:
    """Return the recommendation for a symptom description.

    TODO (Woodey): replace the placeholder below with the real backend:
    red-flag rules first, then the call to Ollama (llama3.2) with prompts/triage.txt.
    Keep the same return format:
        {"appointment_type": "GP", "urgency": "same-day",
         "confidence": "medium", "reason": "one short sentence"}

    PLACEHOLDER ONLY: simple keyword rules so the interface can be shown.
    This is not the AI and must not be used in the M3 demo.
    """
    t = symptoms.lower()
    if any(w in t for w in ("chest pain", "slurred", "can't breathe", "vision")):
        return {"appointment_type": "EMERGENCY", "urgency": "emergency", "confidence": "high",
                "reason": "These symptoms can be a sign of a serious condition."}
    if any(w in t for w in ("runny nose", "sneez", "cold")):
        return {"appointment_type": "SELF_CARE", "urgency": "routine", "confidence": "medium",
                "reason": "This sounds like a common cold."}
    if len(t.split()) < 6:
        return {"appointment_type": "NEEDS_MORE_INFO", "urgency": "routine", "confidence": "low",
                "reason": "Your message is too short to make a safe suggestion."}
    return {"appointment_type": "GP", "urgency": "same-day", "confidence": "medium",
            "reason": "A GP can examine you and refer you if needed."}


@app.route("/", methods=["GET", "POST"])
def index():
    symptoms, result, warning = "", None, None

    if request.method == "POST":
        symptoms = request.form.get("symptoms", "").strip()
        if len(symptoms) < 10:
            warning = "Please describe your symptoms in a few words."
        else:
            result = get_triage(symptoms)
            # Models do not always respect casing (seen in the M2 experiment).
            result["appointment_type"] = str(result.get("appointment_type", "")).upper()
            result["urgency"] = str(result.get("urgency", "")).lower()
            if result["appointment_type"] not in LABELS:
                result["appointment_type"] = "NEEDS_MORE_INFO"

    return render_template("index.html", symptoms=symptoms, result=result,
                           warning=warning, labels=LABELS, urgency=URGENCY)


if __name__ == "__main__":
    app.run(debug=True, port=5000)
