# Digital_Transformation_DeltaTech_Project

**Repository:** https://github.com/Colin-Bastian-James/Digital_Transformation_DeltaTech_Project

## 1. What it does

## 2. Users and value proposition

## 3. How to run it

Requirements: Python 3.9+ and [Ollama](https://ollama.com). Tested on Linux (Fedora).

1. Clone the repository:
   ```bash
   git clone https://github.com/Colin-Bastian-James/Digital_Transformation_DeltaTech_Project.git
   cd Digital_Transformation_DeltaTech_Project
   ```
2. Create a virtual environment and install the dependencies:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate        # Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```
3. Download the local model (about 2 GB) and make sure Ollama is running:
   ```bash
   ollama pull llama3.2
   curl http://localhost:11434      # should print "Ollama is running"; if not, run: ollama serve
   ```
4. Start the web app:
   ```bash
   python app/app.py
   ```
5. Open http://localhost:5000 and describe your symptoms.

No `.env` file is needed: the app uses Ollama at `http://localhost:11434` with `llama3.2` by default. To change this, set the `OLLAMA_URL` / `OLLAMA_MODEL` environment variables (see `.env.example`).

If Ollama is not running, the app still answers: emergency red flags work without the model, and other messages get the safe default ("contact your GP today").

**Optional checks**
- Red-flag tests (no Ollama needed): `python -m unittest discover tests`
- Full evaluation on the 20 test cases (needs Ollama): `python experiment/run_mvp.py`

## 4. Architecture

## 5. AI components: models, APIs, where the prompts live, data sources

## 6. Evaluation: method, results, failure cases

## 7. Limitations, risks, privacy and ethics

## 8. Business case

## 9. AI tools the team used

## 10. Who did what
