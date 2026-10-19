# Sources for the M2 comparison (pricing, tokens, GDPR)

Checked on 2026-10-19. This file backs the claims made in `RESULTS.md`.

## 1. gpt-4o-mini pricing

**Claim:** gpt-4o-mini costs $0.15 per 1M input tokens and $0.60 per 1M output tokens.

- **Primary source:** OpenAI's model page for gpt-4o-mini lists $0.15 / 1M input tokens and $0.60 / 1M output tokens (cached input $0.075 / 1M).
  https://developers.openai.com/api/docs/models/gpt-4o-mini
- **Launch announcement** (July 2024):
  https://openai.com/index/gpt-4o-mini-advancing-cost-efficient-intelligence/

**How the cost per triage was calculated:** published price × average tokens measured in our experiment (308 input, 46 output):
- 308 × $0.15 / 1,000,000 = $0.0000462
- 46 × $0.60 / 1,000,000 = $0.0000276
- Total ≈ **$0.0000738 per triage**, ≈ $0.07 per 1,000 triages.

Nothing was paid. The OpenAI API was never called. Only the local model (llama3.2 via Ollama) was run.

## 2. Why the cost is an estimate (tokenisation)

**Claim:** the token counts come from llama3.2, whose tokenizer is different from gpt-4o-mini's, so the API cost is approximate.

- **Llama 3's tokenizer** has a 128,000-token vocabulary: about 100,000 tokens taken from OpenAI's tiktoken, plus 28,000 added for non-English text.
  https://aiwiki.ai/wiki/llama_3
- **GPT-4o models** use the `o200k_base` tokenizer, with a 200,000-token vocabulary.
  https://leehanchung.github.io/blogs/2024/05/15/gpt-4o-tokenizer/

**Consequence:** the same text is split into a slightly different number of tokens by each model, so the gpt-4o-mini cost is the right order of magnitude but not exact. To get the exact count without paying, count the prompt with OpenAI's open-source `tiktoken` library using the `o200k_base` encoding: https://pypi.org/project/tiktoken/

## 3. GDPR and sending symptoms to an external API provider

**Claim:** sending symptoms to an external API provider is not forbidden, but it is harder to do legally: it needs a valid legal basis for health data, a processor contract, and a lawful transfer mechanism.

This sentence is our own summary of the GDPR articles below; no single article states it in those words. We are not lawyers; this is a course-level reading.

- **Health data is a special category (Article 9(1)).** Processing "data concerning health" is prohibited by default.
  https://gdpr-text.com/en/read/article-9/
- **Exceptions (Article 9(2)).** Examples are *explicit* consent for specified purposes (9(2)(a)), which is stricter than ordinary consent, and processing needed for medical diagnosis or health care under EU or national law by professionals bound by secrecy (9(2)(h)). Same source as above.
- **Processor contract (Article 28(3)).** If OpenAI processes the data on our behalf, the processing must be governed by a written contract that sets out its subject, purpose, data types and the provider's obligations.
  https://gdpr-text.com/en/read/article-28/
- **Transfers outside the EU (Article 44, Chapter V).** Personal data can only go to a non-EU country if the Chapter V conditions are met, so that GDPR protection is not undermined.
  https://gdpr-text.com/en/read/article-44/

**Takeaway for our project:** the API option is legally possible, but it adds requirements:
- explicit consent or another Article 9 basis
- a processor agreement
- a lawful mechanism for any transfer outside the EU

A local model keeps the data inside our own system and avoids these extra requirements. That is why we call it a "GDPR complication", not a "GDPR problem".
