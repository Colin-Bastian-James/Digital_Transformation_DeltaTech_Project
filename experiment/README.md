# M2 experiment — appointment-type triage

Sends 12 fictional patient messages (`cases.json`, no real patient data) to an LLM and checks
whether it recommends the right appointment type: EMERGENCY, OUT_OF_HOURS_GP, GP,
SPECIALIST (only with a referral), SELF_CARE or NEEDS_MORE_INFO.
Cases 3, 5 and 12 come directly from the M1 interviews (ankle injury, referral path,
admitting uncertainty).

Metrics: appointment-type accuracy, urgency accuracy, missed emergencies (safety),
invalid outputs, median and worst latency, tokens per request, and cost per triage
at gpt-4o-mini prices.

## Run it

1. Python 3.9+, no extra packages.
2. Install Ollama (https://ollama.com) and run `ollama pull llama3.2`.
3. From this folder: `python triage_experiment.py --backend ollama --model llama3.2`
4. Optional, API comparison: `export OPENAI_API_KEY=...` then
   `python triage_experiment.py --backend openai --model gpt-4o-mini`
5. Results are saved in `results/<backend>_<model>.json`.

The system prompt is `SYSTEM_PROMPT` at the top of `triage_experiment.py`.
