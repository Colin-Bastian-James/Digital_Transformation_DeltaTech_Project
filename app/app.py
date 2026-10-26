"""DeltaTech Triage Assistant: web interface (MVP).

Run from the repository root:
    python app/app.py
then open http://localhost:5000
"""
from flask import Flask, render_template, request

from triage import get_triage

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
