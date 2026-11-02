"""Run the 12 M2 test cases through the full MVP pipeline (red flags + model).

Compares with the M2 baseline (model only, experiment/results/ollama_llama3.2.json).
Needs Ollama running with llama3.2. From the repository root:
    python experiment/run_mvp.py
Missed emergencies is the most important number. Target: 0.
"""
import json
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "app"))

from triage import get_triage  # noqa: E402

cases = json.loads((ROOT / "experiment" / "cases.json").read_text(encoding="utf-8"))
rows, latencies = [], []
for case in cases:
    start = time.perf_counter()
    result = get_triage(case["symptoms"])
    latency = time.perf_counter() - start
    latencies.append(latency)
    ok = result["appointment_type"] == case["expected_type"]
    missed = case["expected_type"] == "EMERGENCY" and result["appointment_type"] != "EMERGENCY"
    rows.append({"id": case["id"], "expected": case["expected_type"],
                 "got": result["appointment_type"], "source": result["source"],
                 "type_ok": ok, "missed_emergency": missed, "latency_s": round(latency, 2)})
    mark = "OK " if ok else ("!!!" if missed else "ERR")
    print(f"[{mark}] #{case['id']:>2} expected {case['expected_type']:<16} got "
          f"{result['appointment_type']:<16} via {result['source']:<9} ({latency:.1f}s)")

n_emerg = sum(c["expected_type"] == "EMERGENCY" for c in cases)
summary = {
    "pipeline": "red flags + llama3.2 (MVP)",
    "date": time.strftime("%Y-%m-%d"),
    "appointment_type_accuracy": f"{sum(r['type_ok'] for r in rows)}/{len(rows)}",
    "missed_emergencies": f"{sum(r['missed_emergency'] for r in rows)}/{n_emerg}",
    "caught_by_red_flags": sum(r["source"] == "red_flag" for r in rows),
    "fallbacks": sum(r["source"] == "fallback" for r in rows),
    "median_latency_s": round(statistics.median(latencies), 2),
    "worst_latency_s": round(max(latencies), 2),
}
baseline_file = ROOT / "experiment" / "results" / "ollama_llama3.2.json"
if baseline_file.exists():
    b = json.loads(baseline_file.read_text(encoding="utf-8"))["summary"]
    print(f"\nBEFORE (M2, model only): type {b['appointment_type_accuracy']}, "
          f"missed emergencies {b['missed_emergencies']}, median {b['median_latency_s']} s")
print(f"AFTER  (MVP):            type {summary['appointment_type_accuracy']}, "
      f"missed emergencies {summary['missed_emergencies']}, median {summary['median_latency_s']} s")

out = ROOT / "experiment" / "results" / "mvp_red_flags.json"
out.parent.mkdir(exist_ok=True)
out.write_text(json.dumps({"summary": summary, "cases": rows}, indent=2))
print(f"Saved to {out}")
