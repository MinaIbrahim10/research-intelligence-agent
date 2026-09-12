# Architecture

## System overview

Research & Intelligence Agent is an evidence-first agentic research pipeline built around explicit workflow stages, typed boundaries, deterministic guards, and claim-level traceability.

The architecture deliberately separates:

~~~text
Planning
Search
Ranking
Fetching
Evidence extraction
Relevance
Claim consolidation
Verification
Coverage analysis
Reporting
~~~

No single stage is responsible for both discovering evidence and deciding the final answer.

---

## High-level architecture

~~~mermaid
flowchart LR
    U[Browser] --> N[Nginx / React]
    N -->|/api/*| API[FastAPI]

    API --> G[LangGraph Workflow]

    G --> P[Planner]
    P --> S[Search]
    S --> R[Rank + Deduplicate]
    R --> F[Fetch Sources]
    F --> E[Evidence Extraction]
    E --> RG[Relevance Gate]
    RG --> C[Claim Consolidation]
    C --> V[Verification]
    V --> CA[Coverage Analysis]
    CA --> RP[Deterministic Report]

    S --> SX[SearXNG]

    P --> O[Ollama]
    E --> O
    RG --> O
    C --> O
    V --> O

    RP --> API
    API -->|SSE| N
~~~

---

## LangGraph workflow

The production graph executes:

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

Graph nodes update typed application state.

The streaming endpoint consumes LangGraph updates using actual graph execution events and exposes them to the frontend using Server-Sent Events.

---

## Planner

The Planner transforms a user research request into a validated research plan.

Its responsibilities include:

- identifying the research objective,
- producing focused sub-questions,
- suggesting useful source categories,
- identifying freshness requirements,
- defining evidence-oriented success criteria.

The Planner is not allowed to answer the research question.

This prevents premature conclusions before evidence collection.

---

## Search

Search is performed through self-hosted SearXNG.

The search service generates targeted query variants rather than issuing one broad request.

The search layer performs:

- query expansion,
- URL canonicalization,
- tracking-parameter removal,
- global deduplication,
- question-to-source mapping,
- authority classification,
- source ranking.

Source categories can include:

~~~text
government
academic
documentation
repository
news
general_web
~~~

Search infrastructure failure is represented separately from a legitimate empty-result search.

This prevents an unavailable upstream search engine from being interpreted as absence of evidence.

---

## Source ranking

Search results are scored using provider quality and source-authority signals.

Higher-value categories such as official documentation, government resources, academic material, and repositories are favored over lower-authority general web sources when appropriate.

Ranking affects which sources are selected for full-page fetching.

---

## Full-page fetching

Search snippets are not treated as sufficient research evidence.

Selected pages are fetched before evidence extraction.

The fetch layer includes:

- HTTP/HTTPS-only validation,
- hostname and IP validation,
- SSRF protection,
- redirect validation,
- bounded redirects,
- request timeouts,
- maximum response-size limits,
- supported content-type checks,
- text extraction using Trafilatura,
- graceful per-source failure isolation.

One failed page does not terminate an entire research run.

---

## SSRF protection

The fetcher prevents requests to unsafe network destinations.

The protection model rejects addresses such as:

~~~text
localhost
loopback IPs
private internal addresses
non-global resolved IPs
unsafe redirect targets
~~~

Redirect targets are revalidated rather than trusted automatically.

---

## Evidence extraction

The Research stage extracts atomic findings from fetched source content.

It does not decide whether those findings are true.

Grounding invariants include:

1. source IDs must exist,
2. source IDs must belong to fetched sources,
3. evidence excerpts must literally occur in source content after normalization,
4. findings must remain tied to their research question.

The LLM receives bounded page content rather than unrestricted external knowledge.

---

## Evidence relevance gate

Evidence relevance and claim truth are intentionally separated.

The relevance stage asks:

~~~text
Does this evidence directly answer this research question?
~~~

It does not ask:

~~~text
Is this claim ultimately true?
~~~

The gate rejects:

- unrelated products,
- unrelated frameworks,
- generic AI-agent descriptions,
- evidence that discusses the topic but does not answer the requested comparison,
- infrastructure details that do not establish the requested property.

This prevents plausible-but-off-topic evidence from reaching verification.

---

## Claim consolidation

Multiple evidence findings can express the same underlying claim.

The Consolidation stage groups existing finding IDs into consolidated claims.

Important constraints:

- the LLM groups existing findings,
- it does not create arbitrary evidence IDs,
- canonical claim wording remains grounded in existing findings,
- omitted findings fall back to singleton claims,
- evaluator-style claims are protected from being merged into factual capability claims.

This makes verification operate on semantic claims rather than repeated wording.

---

## Claim evidence membership

A consolidated claim contains evidence members.

Conceptually:

~~~text
ConsolidatedClaim
├── finding_ids
├── source_ids
└── members
    ├── finding_id
    ├── source_id
    ├── claim
    ├── evidence_excerpt
    └── evidence_type
~~~

This membership structure becomes the authorization boundary for verification evidence.

---

## Verification

Verification operates per consolidated claim.

Possible statuses:

~~~text
VERIFIED
PARTIALLY_VERIFIED
CONFLICTING
UNSUPPORTED
~~~

The verifier receives evidence relevant to the current claim and research question.

Its output is then constrained by deterministic validation logic.

---

## Sibling-source isolation

A claim can only cite sources belonging to its own evidence members.

For example:

~~~text
Question q1

Claim c1
  sources: s1, s2

Claim c2
  sources: s3
~~~

Claim `c2` cannot cite `s1` or `s2` merely because they appear in the same research question.

This prevents source leakage between sibling claims.

---

## Verification confidence guards

The verification layer applies status and confidence constraints after LLM output.

Examples include:

- `VERIFIED` confidence is capped below perfect certainty,
- `PARTIALLY_VERIFIED` confidence has a lower maximum,
- `UNSUPPORTED` confidence remains low,
- evaluative recommendation claims cannot be promoted to full verification,
- high-risk performance claims require stronger sources,
- missing support forces downgrade to `UNSUPPORTED`.

These constraints prevent the model from using confidence values as unrestricted prose.

---

## Benchmark and performance claims

Claims involving:

~~~text
benchmark
latency
throughput
faster
slower
performance
cost
scalability comparisons
~~~

require stronger corroboration.

Multiple general-web pages repeating similar numbers do not automatically establish independent verification.

Without stronger evidence such claims remain partially verified.

---

## First-party source handling

First-party documentation can strongly establish narrow product facts.

Examples:

~~~text
Framework X supports checkpointing.
Framework Y exposes a routing decorator.
Product Z provides an observability console.
~~~

First-party documentation does not automatically prove comparative conclusions such as:

~~~text
Framework X is faster.
Framework Y is better for production.
Framework Z scales best.
~~~

---

## Coverage analysis

Evidence confidence and comparison coverage are separate metrics.

A question may have strong evidence while still answering only half of a comparison.

Example:

~~~text
Question:
How do LangGraph and CrewAI handle state?

Required:
LangGraph
CrewAI

Usable claims:
LangGraph only
~~~

Coverage becomes:

~~~text
1 / 2 = 50%
~~~

Final question confidence is:

~~~text
Evidence Confidence × Coverage Ratio
~~~

This prevents one-sided research from being presented as a complete comparison.

---

## Entity detection

Coverage analysis identifies explicitly requested entities from research questions and the broader objective.

Comparative language such as:

~~~text
both
each framework
versus
vs
compare
comparison
between
~~~

can cause entities from the research objective to become required coverage targets.

Generic technical terms are excluded from entity requirements.

---

## Reporting

The Report stage is deterministic.

It does not use an LLM to rewrite verification output.

This is an intentional architectural decision.

Allowing another generation step after verification could introduce:

- unsupported wording,
- changed meaning,
- missing caveats,
- citation drift.

Instead, the report formats verified structures directly.

---

## User-facing report contents

Each report can contain:

- overall confidence,
- research-question sections,
- evidence confidence,
- coverage ratio,
- final confidence,
- required entities,
- covered entities,
- verified claims,
- partial claims,
- conflicting claims,
- caveats,
- evidence gaps,
- cited sources.

Unsupported candidate claims are omitted from the main findings list while remaining reflected in gaps and confidence.

---

## Real-time streaming

The research API exposes:

~~~http
POST /api/v1/research/report/stream
~~~

The backend streams Server-Sent Events.

Typical progress stages include:

~~~text
planner
search
fetch_sources
researcher
relevance
consolidator
verifier
reporter
~~~

The frontend receives these events through a streaming `fetch()` request and `ReadableStream`.

`EventSource` is not used because the endpoint requires `POST`.

---

## Frontend architecture

~~~mermaid
flowchart LR
    UI[React UI]
    API[Streaming API Client]
    NG[Nginx]
    BE[FastAPI]

    UI --> API
    API --> NG
    NG -->|/api/*| BE
~~~

Nginx disables proxy buffering for `/api/` so streamed events are forwarded immediately.

The SPA fallback handles frontend routes.

---

## Deployment architecture

~~~mermaid
flowchart TB
    Browser[Browser]

    subgraph Docker Network
        Frontend[React + Nginx]
        Backend[FastAPI]
        Search[SearXNG]
    end

    Ollama[Ollama + GPU on Host]

    Browser -->|127.0.0.1:3000| Frontend
    Frontend --> Backend
    Backend --> Search
    Backend --> Ollama
~~~

Published host ports:

~~~text
Frontend → 127.0.0.1:3000
Backend  → 127.0.0.1:8000
SearXNG  → 127.0.0.1:8080
~~~

These bindings prevent direct LAN exposure through Docker port publishing.

---

## Ollama integration

Ollama remains outside Docker.

Reasons include:

- direct local GPU access,
- reuse of existing local models,
- avoiding duplicate model storage,
- simpler model management.

The backend container reaches the host through:

~~~text
host.docker.internal
~~~

Docker Compose maps this name to the Linux host gateway.

---

## Ollama network hardening

Ollama must listen on an address reachable from Docker.

The host firewall is therefore used to prevent public-zone access while allowing Docker traffic.

Current intended behavior:

~~~text
localhost              → Ollama allowed
Docker bridge network  → Ollama allowed
Wi-Fi public zone      → Ollama blocked
VPN public zone        → Ollama blocked
~~~

Port `11434` is not opened in the public firewalld zone.

---

## Docker health orchestration

The Compose stack defines health checks for:

- SearXNG,
- FastAPI,
- Nginx.

Service ordering is:

~~~text
SearXNG healthy
      ↓
Backend starts
      ↓
Backend healthy
      ↓
Frontend starts
~~~

This avoids startup race conditions where a process exists but its dependency is not ready.

---

## Backend container hardening

The backend production Docker image:

- uses `python:3.14-slim`,
- installs only runtime dependencies,
- excludes pytest and development tooling,
- creates a dedicated application user,
- runs as UID `10001`,
- copies backend files with application-user ownership,
- runs Uvicorn as a non-root process.

Verified runtime identity:

~~~text
uid=10001(appuser)
gid=10001(appuser)
~~~

Verified production dependency state:

~~~text
pytest installed: False
~~~

---

## Dependency model

Development and production dependency environments are separated.

### Development lock

~~~text
requirements.lock.txt
~~~

Contains the fully tested development environment including test tooling.

### Runtime lock

~~~text
requirements.runtime.lock.txt
~~~

Contains the resolved dependency graph required by the backend application only.

### Frontend lock

~~~text
frontend/package-lock.json
~~~

Frontend installation uses:

~~~bash
npm ci
~~~

to preserve reproducibility.

---

## CI architecture

~~~mermaid
flowchart TD
    P[Push / Pull Request]

    P --> B[Backend Tests]
    P --> F[Frontend Quality]

    B --> DB[Docker Build]
    F --> DB

    B --> B1[Install locked deps]
    B1 --> B2[pip check]
    B2 --> B3[pytest]

    F --> F1[npm ci]
    F1 --> F2[npm audit]
    F2 --> F3[oxlint]
    F3 --> F4[Vite build]

    DB --> D1[Backend image]
    DB --> D2[Frontend image]
~~~

CI intentionally avoids requiring Ollama or live SearXNG for deterministic backend unit tests.

---

## Failure philosophy

The system is designed to fail explicitly rather than silently produce confident output.

Examples:

~~~text
Search unavailable
→ explicit search backend failure

Page cannot be fetched
→ source failure recorded

Evidence is irrelevant
→ rejected before verification

Claim has no grounded support
→ UNSUPPORTED

Comparison only covers one entity
→ reduced coverage

Benchmark only has weak sources
→ PARTIALLY_VERIFIED
~~~

The system prefers an incomplete report with visible gaps over a complete-looking report containing unsupported conclusions.

---

## Security boundaries

The primary boundaries are:

~~~text
User input
    ↓
Validated request schema

LLM output
    ↓
Pydantic structured schemas
    ↓
Deterministic ID filtering
    ↓
Evidence/source membership validation

External URL
    ↓
Scheme validation
    ↓
DNS/IP validation
    ↓
Redirect validation
    ↓
Bounded fetch
~~~

These boundaries reduce reliance on model compliance alone.

---

## Current limitations

### Search reliability

Public search engines may:

- rate-limit requests,
- return CAPTCHAs,
- time out,
- behave differently across network or VPN exit IPs.

SearXNG isolates these failures but cannot eliminate upstream restrictions.

### Page parsing

Some sites cannot be extracted reliably because of:

- JavaScript rendering,
- anti-bot protections,
- unusual document structure,
- unsupported content types.

### PDFs

PDF ingestion is not currently a first-class fetch path.

### Evidence quality

The system can only verify against evidence it successfully discovers and fetches.

Low evidence coverage is intentionally surfaced rather than filled using unsupported model knowledge.

---

## Engineering principle

The architecture follows one core rule:

> Every confidence score should represent both the strength of the evidence found and the scope that remains unproven.
