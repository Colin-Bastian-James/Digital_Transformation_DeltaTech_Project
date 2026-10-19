# PROJECT_LOG.md

## 2026-10-12 — M1: Problem & Customer Validation (DeltaTech)

### 1. Problem Statement (≤150 words)
Hospitals and clinics face a persistent challenge: patients often book the wrong type of appointment because they struggle to describe symptoms accurately or understand which medical service they need. This leads to mis‑triaged visits, unnecessary delays, overcrowded general consultations, and increased administrative workload. Patients frequently choose inappropriate appointment types, resulting in longer waiting times, rescheduling, and inefficient use of medical staff. For healthcare providers, each mis‑triaged appointment can cost 10–30 minutes of administrative correction and disrupt scheduling. For patients, it increases anxiety, prolongs care, and can delay access to the right specialist. Today, triage is either done manually by reception staff or left entirely to patients navigating complex online booking systems. A simple, AI‑enabled triage assistant could significantly reduce mis‑bookings, improve patient flow, and save time for both patients and medical staff.

### 2. Users and Customers
**Primary users:** Patients seeking medical appointments, especially those unsure which specialist or service they need.  
**Customers:** Hospitals, clinics, and medical practices that want to reduce mis‑triaged appointments and administrative load.  
**Segment & size:** Luxembourg has ~630,000 residents (STATEC, 2026). Around 90% use digital appointment systems yearly. Hospitals and clinics represent ~50 major providers nationwide.

### 3. Interview Notes

#### Interview 1 (marique-gabriel)
**Role:** patient access manager receptionist
**Date:** 03 Oct 2026
**Duration:** 15 minutes
**Notes:**  
- Point 1 :
    **Misrouting costs the hospital, not only the patient.** Saturated phone lines, wasted consultation slots and avoidable emergency visits.
- Point 2 :
    **There is an orientation gap.** Front-desk staff cannot give medical advice, which leaves patients between "call the hospital" and "see your GP".

- Point 3 :
    **The tool must respect the referral path.** Sending patients to specialists without the required prescription shifts work to the hospital instead of removing it.
- Point 4 :
    **Adoption requires trust and compliance.** Physician validation, emergency handling, GDPR compliance and clear liability are preconditions.

- Point 5 :
    **User and customer are different.** Patients use the tool; the hospital or public health authorities would pay, and the purchase involves several decision-makers.

#### Interview 2 (ajavon-woodey)
**Role:** Patient with ankle injury
**Date:**  11 Oct 2026
**Duration:** 25 minutes
**Notes:**  
- Point 1 : 
    Twisted his ankle playing football; unsure whether it was a simple sprain or needed an X-ray or a specialist.
- Point 2 :
    Did not know whether to go to his GP, a sports doctor or the emergency department; asked a teammate and searched online, then chose his GP. The uncertainty makes him tempted to go straight to A&E.
- Point 3 : 
    Online symptom searches helped him prepare questions but listed many possible causes and made him more uncertain.
- Point 4 : 
    Would trust an app that asks simple questions, explains its recommendation, admits uncertainty and sends him to urgent care when needed; would distrust a confident diagnosis or one that pushes a specific provider.
- Point 5 : 
    Would not pay a subscription: expects the service to be free, offered by a hospital, mutuality or insurer → the patient is the user, not the payer.

### 4. Existing Alternatives
- **Manual triage by reception staff:** Accurate but slow, costly, and limited to office hours.  
- **Self‑booking through hospital portals:** Fast but confusing; high rate of mis‑triage.  
- **Doing nothing / guessing:** Leads to wrong appointments, delays, and frustration.

### 5. Value Proposition (one sentence)
For patients who struggle to choose the correct medical appointment, DeltaTech Triage Assistant is an AI‑enabled symptom‑guidance tool that recommends the right appointment type instantly, unlike manual triage or confusing self‑booking portals.

### 6. Why AI (≤80 words)
AI enables fast, accurate interpretation of patient‑described symptoms, something difficult for rule‑based systems. Without AI, triage would require manual staff intervention or rigid questionnaires that fail to capture nuance. AI allows natural language input, adapts to varied symptom descriptions, and provides reliable recommendations at scale. It reduces administrative load and improves patient flow in ways traditional systems cannot.


## 2026-10-19 — M2: Technology exploration and project proposal

### 1. Two candidate approaches compared
| Criterion | A. API model: gpt-4o-mini (OpenAI) | B. Local model: llama3.2 3B (Ollama) |
|---|---|---|
| Output quality | Not measured (no API key yet). Larger model, expected to handle subtle red flags better. | Measured: 9/12 appointment type, 7/12 urgency, 1/4 emergencies missed. |
| Cost per triage | ≈ $0.000074, i.e. ≈ $0.07 per 1,000 triages | $0 per request. Fixed cost instead: a server to run the model once deployed. |
| Latency | Not measured; published ≈ 0.6 s to first token | Measured on laptop CPU: 7.1 s median, 8.3 s worst |
| Data needed | No training data, only the prompt | No training data, only the prompt |
| Failure modes | Outages and rate limits; health data (GDPR special category) leaves our system and is sent to an external provider | Misses subtle emergencies, over-triages; slow on weak hardware |
| Vendor lock-in | Medium: OpenAI-specific API and pricing | Low: open weights, model swappable with `--model` |

### 2. Experiment
- **Location:** `experiment/` (script, 12 test cases, run instructions in `experiment/README.md`, raw results in `experiment/results/`).
- **Task:** recommend an appointment type (EMERGENCY, OUT_OF_HOURS_GP, GP, SPECIALIST, SELF_CARE, NEEDS_MORE_INFO) and urgency for 12 fictional patient messages.
- **Result (llama3.2, 2026-10-19):** 9/12 correct appointment type, 7/12 correct urgency, 1/4 emergencies missed, 0 invalid outputs, median latency 7.1 s.
- **Sample outputs and commentary:** see `experiment/RESULTS.md` (case 3 correct, case 10 missed emergency, case 12 does not ask for more information).

### 3. Chosen approach, limitations, switch conditions
- **Chosen approach:** B. Local model (llama3.2 3B via Ollama), with a rule-based red-flag layer in front of it.
- **Why:** patient symptoms are health data, a GDPR special category. With a local model, no patient message leaves our system, which removes the main legal and trust barrier for a hospital customer. Vendor lock-in stays low (open weights, model swappable).
- **Not chosen for cost:** at our measured token counts the API is cheaper per triage until very high volumes (see §5).

**Three limitations**
1. **Missed emergencies:** 1/4 emergencies missed in the experiment. Mitigation for the MVP: hard-coded red-flag rules (chest pain, breathing difficulty, stroke signs → EMERGENCY / call 112) run before the model, so the model can never downgrade them.
2. **Latency:** 7.1 s median on a laptop CPU, and slower with several users at once. Production needs a dedicated server, possibly with a GPU.
3. **Limited quality and languages:** a 3B model struggles with vague descriptions (7/12 correct urgency), and Luxembourgish is not supported.

**What would make us switch to an API model**
- After adding the red-flag rules, the local model still misses an emergency on an extended test set (≥ 20 cases).
- Median latency above 10 s with real test users.
- A provider offers EU-only processing with a data processing agreement acceptable to a hospital.

### 4. Architecture sketch
- **Image:** `docs/Architecture-M2.png` (source: `docs/architecture-m2.mmd`).
- **Flow:** patient web page → Python backend → red-flag rules → if no red flag, Ollama server (llama3.2 3B) with the prompt from `prompts/triage.txt` → appointment type, urgency and reason back to the patient.
- **Secrets and config:** `.env`, git-ignored; `.env.example` committed.
- **Data boundary:** everything runs on our server; no patient data is sent to a third party.

### 5. Cost estimate
gpt-4o-mini, OpenAI list price checked 2026-10-19: $0.15 / 1M input tokens, $0.60 / 1M output tokens.
- 308 input tokens × $0.15 / 1,000,000 = $0.0000462
- 46 output tokens × $0.60 / 1,000,000 = $0.0000276
- **Total per triage = $0.0000738** (token counts measured in the experiment)

**Model update** : `gpt-4o-mini` is deprecated; the snapshot `gpt-4o-mini-2024-07-18` shuts down on 14 Jan 2027. OpenAI's recommended replacement is `gpt-6-luna`, list price checked 2026-10-19: $0.10 / 1M input, $0.50 / 1M output.
- 308 input tokens × $0.10 / 1,000,000 = $0.0000308
- 46 output tokens × $0.50 / 1,000,000 = $0.0000230
- **Total per triage = $0.0000538**

**Local option, chosen** : no per-request cost, fixed server cost instead.
- Hetzner Cloud CPX32 (4 vCPU, 8 GB RAM, EU), price read from Hetzner's price API on 2026-10-07: **€35.99 / month**. 8 GB leaves room for llama3.2 3B (≈ 3–4 GB) plus the backend.
- At 1,000 triages / month: €35.99 / 1,000 = **≈ €0.036 per triage**
- Break-even vs gpt-6-luna: 35.99 / 0.0000538 = **≈ 670,000 triages / month** (treating € ≈ $ for an order of magnitude)
- Conclusion: the local model costs more at low volume; we accept this in exchange for keeping health data in-house.

### 6. Plan to the MVP
**Our MVP plan runs until 16 Nov:**
- By 26 Oct: Basic web UI for symptom input (Gabriel Marique)
- By 26 Oct: Backend endpoint calling the local llama3.2 model (Woodey Ajavon)
- By 02 Nov: Implement red‑flag rule layer and connect it to the triage flow (Woodey Ajavon)
- By 09 Nov: Test with ≥20 symptom cases and refine prompts (Gabriel Marique + Bastian-James Colin)
- By 16 Nov: Prepare demo scenario, example cases, and running MVP for M3 (whole team)

### 7. Repository
Repository created, README skeleton in place, `.env.example` committed, `.env` git-ignored.

### Notes on M1 to address in the final package
- Interview 1 lasted 15 min; the spec asks for about 20–30 min. Consider one additional, longer interview.
- "Around 90% use digital appointment systems yearly" needs a source and date.
