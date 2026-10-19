"""M2 experiment - DeltaTech Triage Assistant.

Asks an LLM to recommend the right appointment type for 12 fictional patient
messages and scores it against the expected answer. Compares a local model
(Ollama) with an API model (gpt-4o-mini). Standard library only.

    python triage_experiment.py --backend ollama --model llama3.2
    python triage_experiment.py --backend openai --model gpt-4o-mini   # needs OPENAI_API_KEY
"""
import argparse
import json
import os
import statistics
import time
import urllib.request
from pathlib import Path

HERE = Path(__file__).parent

APPOINTMENT_TYPES = {
    "EMERGENCY": "go to the emergency department or call 112 now",
    "OUT_OF_HOURS_GP": "on-call GP (maison medicale de garde) when the regular GP is closed",
    "GP": "appointment with a general practitioner",
    "SPECIALIST": "specialist appointment, only if the patient already has a referral",
    "SELF_CARE": "pharmacist advice and self-care, no appointment needed",
    "NEEDS_MORE_INFO": "the message is too vague; ask a follow-up question",
}
URGENCIES = ["emergency", "same-day", "routine"]

# OpenAI list price for gpt-4o-mini, USD per 1M tokens, checked 2026-10-19.
PRICE_IN, PRICE_OUT = 0.15, 0.60

# The prompt lives here so it is versioned with the code.
SYSTEM_PROMPT = (
    "You are a triage assistant for a hospital booking service in Luxembourg. "
    "You do not diagnose. You recommend which type of appointment the patient should book.\n"
    "Appointment types:\n"
    + "\n".join(f"- {k}: {v}" for k, v in APPOINTMENT_TYPES.items())
    + "\nRules:\n"
    "1. Any possibly life-threatening symptom -> EMERGENCY. When in doubt between EMERGENCY and something else, choose EMERGENCY.\n"
    "2. Do not send patients to a SPECIALIST unless they say they already have a referral; otherwise choose GP.\n"
    "3. If the message is too vague to decide, choose NEEDS_MORE_INFO.\n"
    "Urgency: emergency (now), same-day (today), routine (normal booking).\n"
    'Answer ONLY with JSON: {"appointment_type": "...", "urgency": "...", '
    '"confidence": "high|medium|low", "reason": "one short sentence for the patient"}'
)


def post_json(url, payload, headers=None):
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json", **(headers or {})},
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        return json.loads(resp.read())


def messages_for(symptoms):
    return [{"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": symptoms}]


def ask_ollama(model, symptoms):
    data = post_json("http://localhost:11434/api/chat", {
        "model": model, "stream": False, "format": "json",
        "options": {"temperature": 0}, "messages": messages_for(symptoms),
    })
    return data["message"]["content"], data.get("prompt_eval_count", 0), data.get("eval_count", 0)


def ask_openai(model, symptoms):
    key = os.environ.get("OPENAI_API_KEY")
    if not key:
        raise SystemExit("Set OPENAI_API_KEY first (export it, or put it in the git-ignored .env).")
    data = post_json(
        "https://api.openai.com/v1/chat/completions",
        {"model": model, "temperature": 0, "response_format": {"type": "json_object"},
         "messages": messages_for(symptoms)},
        headers={"Authorization": f"Bearer {key}"},
    )
    usage = data.get("usage", {})
    return (data["choices"][0]["message"]["content"],
            usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0))


def main():
    parser = argparse.ArgumentParser(description="Run the DeltaTech triage experiment.")
    parser.add_argument("--backend", choices=["ollama", "openai"], default="ollama")
    parser.add_argument("--model", default="llama3.2")
    args = parser.parse_args()
    ask = ask_ollama if args.backend == "ollama" else ask_openai

    cases = json.loads((HERE / "cases.json").read_text())
    rows, latencies = [], []
    for case in cases:
        start = time.perf_counter()
        raw, t_in, t_out = ask(args.model, case["symptoms"])
        latency = time.perf_counter() - start
        latencies.append(latency)
        try:
            answer = json.loads(raw)
            valid = answer.get("appointment_type") in APPOINTMENT_TYPES
        except json.JSONDecodeError:
            answer, valid = {"reason": raw[:120]}, False
        got_type, got_urg = answer.get("appointment_type"), answer.get("urgency")
        type_ok = got_type == case["expected_type"]
        urg_ok = str(got_urg).lower() == case["expected_urgency"]
        # Safety: a real emergency that the model did not send to EMERGENCY.
        missed_emergency = case["expected_type"] == "EMERGENCY" and got_type != "EMERGENCY"
        rows.append({**case, "got_type": got_type, "got_urgency": got_urg,
                     "confidence": answer.get("confidence"), "reason": answer.get("reason"),
                     "valid_output": valid, "type_ok": type_ok, "urgency_ok": urg_ok,
                     "missed_emergency": missed_emergency, "latency_s": round(latency, 2),
                     "tokens_in": t_in, "tokens_out": t_out})
        mark = "OK " if type_ok else ("!!!" if missed_emergency else "ERR")
        print(f"[{mark}] #{case['id']:>2} expected {case['expected_type']}/{case['expected_urgency']}"
              f"  got {got_type}/{got_urg}  ({latency:.1f}s)")

    n = len(rows)
    avg_in = sum(r["tokens_in"] for r in rows) / n
    avg_out = sum(r["tokens_out"] for r in rows) / n
    summary = {
        "backend": args.backend,
        "model": args.model,
        "date": time.strftime("%Y-%m-%d"),
        "cases": n,
        "appointment_type_accuracy": f"{sum(r['type_ok'] for r in rows)}/{n}",
        "urgency_accuracy": f"{sum(r['urgency_ok'] for r in rows)}/{n}",
        "missed_emergencies": f"{sum(r['missed_emergency'] for r in rows)}/{sum(c['expected_type'] == 'EMERGENCY' for c in cases)}",
        "invalid_outputs": sum(not r["valid_output"] for r in rows),
        "median_latency_s": round(statistics.median(latencies), 2),
        "worst_latency_s": round(max(latencies), 2),
        "avg_tokens_in": round(avg_in),
        "avg_tokens_out": round(avg_out),
        "gpt4o_mini_cost_per_triage_usd": round(avg_in * PRICE_IN / 1e6 + avg_out * PRICE_OUT / 1e6, 7),
    }
    print("\n" + json.dumps(summary, indent=2))

    out_dir = HERE / "results"
    out_dir.mkdir(exist_ok=True)
    out_file = out_dir / f"{args.backend}_{args.model.replace(':', '-').replace('/', '-')}.json"
    out_file.write_text(json.dumps({"summary": summary, "prompt": SYSTEM_PROMPT, "cases": rows}, indent=2))
    print(f"Saved to {out_file}")


if __name__ == "__main__":
    main()
