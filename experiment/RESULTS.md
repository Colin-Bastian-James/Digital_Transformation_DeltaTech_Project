# M2 experiment results — 2026-10-19

Model: llama3.2 (3B) via Ollama, run locally on an HP Pavilion laptop. 12 fictional cases, temperature 0.
Raw output: `results/ollama_llama3.2.json`.

| Metric | Result |
|---|---|
| Appointment type correct | 9/12 (75%) |
| Urgency correct | 7/12 (58%) |
| Missed emergencies | 1/4 |
| Invalid outputs | 0/12 |
| Latency, median / worst | 7.1 s / 8.3 s |
| Tokens per request, in / out | 308 / 46 |

## Sample outputs with commentary

**Case 3 — correct (ankle injury, from interview 2).** "Twisted my ankle playing football, swollen but I can still walk on it." → GP, same-day. This is the right answer: a GP can examine it and prescribe an X-ray, which avoids an unnecessary emergency visit. The model handles the main scenario from our patient interview.

**Case 10 — dangerous failure (missed emergency).** "Sudden flashes of light and a dark curtain over part of my vision." → NEEDS_MORE_INFO instead of EMERGENCY. These are signs of a possible retinal detachment, which needs treatment within hours. The prompt rule "life-threatening → EMERGENCY" was not enough because the symptoms do not sound dramatic. This shows that the MVP cannot rely on the LLM alone for red flags: we need a rule-based safety net (keyword list of red-flag symptoms checked before and after the model) and more emergency examples in the prompt.

**Case 12 — fails to admit uncertainty.** "I just don't feel well." → GP, routine, instead of asking a follow-up question. GP is a safe default, but interview 2 said patients trust a tool that admits when it is unsure. For the MVP, the assistant should ask 2-3 follow-up questions (where, since when, how bad) before recommending.

## Overall pattern
The model over-triages: routine cases often come back as "same-day" and a common cold (case 8) was sent to a GP instead of self-care. Over-triage is the safe direction to be wrong, but it wastes appointment slots, which is the problem our product claims to solve. The 3B model is fast and free to run, but its accuracy is borderline for a health use case.
