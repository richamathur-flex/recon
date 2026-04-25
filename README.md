# Recon

> Autonomous research agent platform — competitive intelligence and equity research, orchestrated by LLM agents over hybrid retrieval.

**Status:** 🟡 Active development · Day 2 of 14 · Agent #1 working

## What is this?

Recon is a Python application that behaves like a junior research analyst. Send it a natural-language question through Slack — *"Tell me about Linear"* — and it autonomously fetches data from web sources, analyzes it with LLM agents, and returns a structured research brief.

## Current capabilities

- **Web Intelligence Agent** — extracts a company's value proposition, target customer, and key features from their homepage. Validated on 7 companies (Linear, Notion, Stripe, Supabase, Airtable, Figma, Vercel).
- **Hybrid retrieval foundation** — Pinecone + Nomic embeddings, smoke-tested end-to-end.
- **Type-safe configuration** — Pydantic Settings, validated at startup.

## Tech stack

| Layer | Choice |
|---|---|
| LLM | Groq (Llama 3.3 70B) |
| Vector DB | Pinecone (serverless) |
| Embeddings | Nomic Embed Text v1.5 (local) |
| Validation | Pydantic v2 |
| HTTP | httpx |
| HTML parsing | selectolax |

## Documentation

Full project dossier (architecture, journey, agent design, learning resources) lives at [`docs/index.html`](docs/index.html) — open it locally in a browser.

## Running locally

```bash
# Setup
python -m venv .venv
.venv\Scripts\Activate.ps1     # Windows PowerShell
pip install -r requirements.txt

# Configure
cp .env.template .env          # then add your GROQ_API_KEY and PINECONE_API_KEY

# Run smoke test
python scripts/smoke_test.py

# Run the agent on any company
python -m scripts.run_web_intel https://linear.app Linear
```

## Roadmap

- [x] Day 1 — Project foundation, smoke test, GitHub setup
- [x] Day 2 — Web Intelligence Agent (7 companies tested)
- [ ] Day 3 — Vector store abstraction (Pinecone + Qdrant Protocol)
- [ ] Day 4 — Document chunking and embedding pipeline
- [ ] Day 5–6 — Hiring Signals Agent (Greenhouse/Lever APIs)
- [ ] Day 7–8 — LangGraph orchestration
- [ ] Day 9–10 — Slack Bolt interface
- [ ] Day 11 — FastAPI REST endpoint
- [ ] Day 12 — Cloud deployment (Fly.io + Render)
- [ ] Day 13 — Tests + RAGAS evaluation in CI
- [ ] Day 14 — Polish and demo

## Author

[Richa Mathur](https://github.com/richamathur-flex)