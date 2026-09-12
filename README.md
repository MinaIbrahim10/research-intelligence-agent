# Research & Intelligence Agent

An evidence-first agentic research system that turns an open-ended research question into a structured, cited report with claim-level traceability, verification, coverage-aware confidence, and explicit research gaps.

Instead of asking one LLM call to "research and answer", the system separates planning, search, source fetching, evidence extraction, relevance filtering, claim consolidation, verification, coverage analysis, and reporting into explicit stages.

---

## Overview

Given a research question, the system:

- decomposes the request into focused research questions,
- searches the web through a self-hosted SearXNG instance,
- ranks and deduplicates candidate sources,
- fetches and extracts full-page content,
- extracts literal evidence from fetched pages,
- filters evidence for question-level relevance,
- consolidates semantically related findings into claims,
- verifies each claim against its own supporting evidence,
- identifies unsupported and conflicting claims,
- measures comparison coverage,
- computes coverage-adjusted confidence,
- produces a cited final report,
- streams real LangGraph execution progress to the frontend.

---

## Why this is not just a chatbot

The pipeline enforces explicit boundaries between research responsibilities.

The **Planner** does not answer the research question.

The **Research stage** extracts evidence but does not decide whether a claim is true.

The **Relevance stage** decides whether evidence answers the target question, not whether it is factually correct.

The **Verification stage** cannot borrow evidence from unrelated claims.

The **Report stage** is deterministic and renders grounded verification results instead of asking another LLM to rewrite them.

This makes evidence provenance, uncertainty, missing coverage, and unsupported claims visible instead of hiding them behind fluent generated text.

---

## Research pipeline

~~~mermaid
flowchart TD
    A[User Query] --> B[Planner]
    B --> C[Search]
    C --> D[Ranking & Deduplication]
    D --> E[Full-page Fetch]
    E --> F[Evidence Extraction]
    F --> G[Evidence Relevance Gate]
    G --> H[Claim Consolidation]
    H --> I[Verification]
    I --> J[Coverage Analysis]
    J --> K[Deterministic Report]
    K --> L[React Frontend]

    C --> S[SearXNG]

    B --> O[Ollama]
    F --> O
    G --> O
    H --> O
    I --> O
~~~

---

## LangGraph workflow

The production workflow executes:

~~~text
START
  ↓
planner
  ↓
search
  ↓
fetch_sources
  ↓
researcher
  ↓
relevance
  ↓
consolidator
  ↓
verifier
  ↓
reporter
  ↓
END
~~~

Each node operates on typed graph state and has a clearly defined responsibility.

---

## Real agent execution

The frontend does not simulate progress with timers.

The endpoint:

~~~http
POST /api/v1/research/report/stream
~~~

streams Server-Sent Events generated from actual LangGraph node updates.

The interface reflects real execution stages:

~~~text
Planning research questions
→ Searching the web
→ Fetching full pages
→ Extracting evidence
→ Filtering relevance
→ Consolidating claims
→ Verifying claims
→ Building final report
~~~

The progress UI advances only when the corresponding graph stage actually runs.

---

## Evidence grounding

Evidence extraction is constrained by deterministic guards.

A finding is accepted only when:

1. its source ID exists,
2. the referenced source was actually fetched,
3. the normalized evidence excerpt literally appears in fetched source content,
4. the evidence is relevant to the target research question.

The evidence layer therefore extracts from supplied page content instead of silently relying on model memory.

---

## Evidence relevance gate

Relevance is evaluated separately from truth.

The gate is designed to reject:

- unrelated framework drift,
- unrelated vendors,
- generic AI-agent statements that do not answer the question,
- infrastructure facts that do not establish the requested comparison,
- evidence attached to the wrong research question.

This prevents irrelevant but plausible-looking material from entering the verification stage.

---

## Claim consolidation

Related evidence findings can be grouped into consolidated claims.

The LLM may group existing finding IDs, but it cannot freely invent a new evidence basis.

Canonical claim text remains grounded in existing findings.

The system also protects against unsafe merging of factual claims with evaluative claims such as:

~~~text
best
better
recommended
ideal
faster
slower
cheaper
~~~

---

## Verification model

Claims are classified as:

- `VERIFIED`
- `PARTIALLY_VERIFIED`
- `CONFLICTING`
- `UNSUPPORTED`

Verification includes deterministic safety guards such as:

- claim-level source isolation,
- no hallucinated source IDs,
- no verified or partially verified claim without a supporting citation,
- subjective recommendation claims cannot become fully verified,
- high-risk benchmark and performance claims require stronger corroboration,
- conflicting status requires actual contradictory evidence,
- unsupported candidates remain visible through gaps and confidence rather than being promoted into findings.

---

## Claim-level source isolation

Each consolidated claim may only cite sources that belong to that claim's own evidence members.

For example:

~~~text
Claim A
 ├── Evidence A1
 └── Evidence A2

Claim B
 └── Evidence B1
~~~

Claim B cannot cite Evidence A1 or Evidence A2.

This prevents strong evidence from one claim from leaking into another claim within the same research question.

---

## First-party evidence

First-party documentation and repositories receive special treatment only for narrow product-capability claims.

Official documentation may strongly establish that a framework exposes a specific feature.

Comparative or evaluative statements such as:

~~~text
faster
better
recommended
lower latency
higher throughput
best for production
~~~

require stronger or independent corroboration.

---

## Coverage-aware confidence

Evidence confidence alone is not enough for comparison research.

If a question asks about both LangGraph and CrewAI but usable evidence only covers one framework, the system records partial coverage and reduces final confidence accordingly.

Conceptually:

~~~text
Final Question Confidence
    =
Evidence Confidence
    ×
Coverage Ratio
~~~

Example:

~~~text
Required entities: LangGraph, CrewAI
Covered entities:  LangGraph
Coverage:          50%
~~~

Overall report confidence is calculated across research questions so one strongly researched section cannot hide an unanswered comparison dimension.

---

## Deterministic reporting

The final Report stage does not ask an LLM to rewrite verified claims.

It deterministically transforms verification output into the user-facing report.

The report includes:

- claim verification status,
- grounded citations,
- caveats,
- evidence gaps,
- required entities,
- covered entities,
- evidence confidence,
- coverage,
- final confidence,
- cited source list.

Unsupported candidate claims still influence gaps and confidence but are not displayed as normal findings.

---

## Search and source discovery

Search is performed through a self-hosted SearXNG instance.

The search layer includes:

- targeted query variants,
- canonical URL normalization,
- tracking-parameter removal,
- global deduplication,
- question-to-source mapping,
- source-category classification,
- authority-aware ranking,
- graceful engine failure handling.

The system distinguishes between:

~~~text
No useful results
~~~

and:

~~~text
Search backend unavailable
~~~

so upstream engine failures are not mistaken for legitimate evidence absence.

---

## Full-page fetching

Selected search results are fetched before evidence extraction.

The fetch layer includes:

- HTTP/HTTPS validation,
- SSRF protection,
- redirect validation,
- request timeouts,
- response-size limits,
- content-type checks,
- full-page extraction with Trafilatura,
- graceful per-source failure handling.

An individual page failure does not terminate the entire research run.

---

## Frontend

The frontend is built with React and Vite and served through Nginx in production.

Features include:

- research query input,
- real agent execution status,
- progress bar,
- stage-level progress indicators,
- overall confidence,
- evidence confidence,
- comparison coverage,
- verification badges,
- citations,
- caveats,
- evidence gaps,
- source links,
- Markdown copy/download,
- responsive dark interface.

The production Nginx configuration disables buffering for the streaming endpoint so Server-Sent Events reach the UI immediately.

---

## Tech stack

### Backend

- Python 3.14
- FastAPI
- LangGraph
- Pydantic v2
- HTTPX
- Trafilatura
- pytest

### Research and AI

- Ollama
- `gemma4:e4b`
- self-hosted SearXNG
- structured LLM outputs
- deterministic grounding and verification guards

### Frontend

- React 19
- Vite 8
- Nginx
- Lucide React
- Server-Sent Events

### Infrastructure

- Docker Compose
- container health checks
- non-root backend container
- runtime-only backend dependencies
- GitHub Actions CI
- localhost-only published application ports
- host firewall hardening

---

## Deployment architecture

~~~mermaid
flowchart TB
    U[Browser]

    subgraph Docker
        FE[React + Nginx<br/>127.0.0.1:3000]
        BE[FastAPI<br/>127.0.0.1:8000]
        SX[SearXNG<br/>127.0.0.1:8080]
    end

    OL[Ollama + Local GPU<br/>Host :11434]

    U --> FE
    FE -->|/api/*| BE
    BE --> SX
    BE --> OL
~~~

Ollama remains on the host so it can use the local GPU directly.

The backend container reaches Ollama through:

~~~text
host.docker.internal
~~~

---

## Docker deployment

### Requirements

- Docker
- Docker Compose
- Ollama
- the configured local model

Create the environment file:

~~~bash
cp .env.example .env
~~~

Ensure the configured model exists:

~~~bash
ollama list
~~~

The current default model is:

~~~text
gemma4:e4b
~~~

Start the complete stack:

~~~bash
docker compose up -d --build
~~~

Check health:

~~~bash
docker compose ps
~~~

Expected services:

~~~text
research-intelligence-searxng
research-intelligence-backend
research-intelligence-frontend
~~~

Expected status:

~~~text
SearXNG   healthy
Backend   healthy
Frontend  healthy
~~~

Open:

~~~text
Frontend: http://127.0.0.1:3000
API docs: http://127.0.0.1:8000/docs
SearXNG:  http://127.0.0.1:8080
~~~

---

## Ollama and Docker on Linux

The backend container needs network access to Ollama running on the host.

The Docker Compose configuration maps:

~~~text
host.docker.internal → host-gateway
~~~

If Ollama only listens on:

~~~text
127.0.0.1:11434
~~~

Docker containers cannot reach it.

For a local Linux development machine, Ollama can be configured to listen on:

~~~text
0.0.0.0:11434
~~~

while the host firewall blocks public-zone access to port `11434`.

Do not expose an unauthenticated Ollama endpoint to untrusted networks.

---

## Local development

Create the environment:

~~~bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.lock.txt
~~~

Start the backend:

~~~bash
uvicorn app.main:app \
  --app-dir backend \
  --reload
~~~

Start the frontend:

~~~bash
cd frontend
npm ci
npm run dev
~~~

Development frontend:

~~~text
http://127.0.0.1:5173
~~~

---

## API

Interactive API documentation:

~~~text
http://127.0.0.1:8000/docs
~~~

Core endpoints include:

~~~http
POST /api/v1/research/plan
POST /api/v1/research/search
POST /api/v1/research/report/stream
~~~

The streaming report endpoint executes the complete research graph and streams real workflow progress before returning the final structured report.

---

## Testing

Backend:

~~~bash
pytest -q
~~~

Frontend:

~~~bash
cd frontend
npm ci
npm run lint
npm run build
~~~

Python dependency validation:

~~~bash
python -m pip check
~~~

Frontend dependency audit:

~~~bash
cd frontend
npm audit
~~~

The backend test suite uses controlled LLM fakes where appropriate so deterministic unit tests do not depend on live external research services.

---

## Continuous integration

GitHub Actions runs on pushes and pull requests.

The CI workflow performs:

~~~text
Backend dependency installation
→ Python dependency validation
→ Backend tests

Frontend dependency installation
→ Dependency audit
→ Lint
→ Production build

Then:

Backend Docker image build
→ Frontend Docker image build
~~~

Workflow:

~~~text
.github/workflows/ci.yml
~~~

---

## Container security

The backend production image:

- runs as a dedicated non-root user,
- uses UID `10001`,
- installs runtime dependencies only,
- does not contain pytest or test tooling,
- uses a separate runtime dependency lock,
- publishes the API only to localhost.

Verified runtime identity:

~~~text
uid=10001(appuser)
~~~

Verified production image state:

~~~text
pytest installed: False
~~~

Published application ports are bound to localhost:

~~~text
127.0.0.1:3000 → frontend
127.0.0.1:8000 → backend
127.0.0.1:8080 → SearXNG
~~~

---

## Health orchestration

Docker Compose defines health checks for:

- SearXNG,
- FastAPI,
- frontend Nginx.

Startup ordering is based on service health:

~~~text
SearXNG healthy
      ↓
Backend healthy
      ↓
Frontend starts
~~~

This avoids considering a service ready merely because its process exists.

---

## Dependency strategy

Two Python lock files are intentionally maintained:

~~~text
requirements.lock.txt
requirements.runtime.lock.txt
~~~

`requirements.lock.txt` represents the tested development environment and includes test tooling.

`requirements.runtime.lock.txt` contains only dependencies required by the production backend image.

The frontend uses:

~~~text
frontend/package-lock.json
~~~

and production builds use:

~~~bash
npm ci
~~~

for reproducible installation.

---

## Project structure

~~~text
research-intelligence-agent/
├── backend/
│   ├── app/
│   │   ├── agents/
│   │   ├── api/
│   │   ├── graph/
│   │   ├── providers/
│   │   ├── schemas/
│   │   ├── services/
│   │   ├── tools/
│   │   ├── config.py
│   │   └── main.py
│   ├── tests/
│   └── Dockerfile
├── frontend/
│   ├── public/
│   │   └── favicon.svg
│   ├── src/
│   │   ├── api/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   └── styles.css
│   ├── Dockerfile
│   ├── nginx.conf
│   ├── package.json
│   └── package-lock.json
├── infra/
│   └── searxng/
│       └── config/
├── docs/
│   ├── architecture.md
│   └── milestone-1.md
├── .github/
│   └── workflows/
│       └── ci.yml
├── .dockerignore
├── .env.example
├── .gitignore
├── docker-compose.yml
├── docker-compose.searxng.yml
├── pyproject.toml
├── requirements.lock.txt
├── requirements.runtime.lock.txt
└── README.md
~~~

---

## Current limitations

The quality of a report depends on accessible web evidence.

Search engines can rate-limit or challenge requests.

Some pages may fail to fetch or parse.

PDF ingestion is not yet a first-class source-fetching path.

A partially verified claim means that available evidence supports the claim but does not provide enough independent corroboration for full verification.

Low comparison coverage is intentionally surfaced rather than compensated for using unsupported model knowledge.

---

## Historical development

The project began with a Planner-only milestone and progressively added:

~~~text
Planner
→ Search
→ Fetching
→ Evidence extraction
→ Relevance filtering
→ Claim consolidation
→ Verification
→ Coverage analysis
→ Reporting
→ Frontend
→ Real LangGraph streaming
→ Docker deployment
→ Production hardening
→ CI
~~~

The original Planner milestone is preserved in:

~~~text
docs/milestone-1.md
~~~

as a record of the project's incremental engineering process.

---

## Design principle

> Evidence first. Confidence must reflect both what the system established and what it failed to establish.
