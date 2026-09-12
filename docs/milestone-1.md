# Milestone 1 — Planner Core

This document is preserved as a historical record of the first implementation milestone.

The production system has since expanded far beyond this milestone.

## Original Definition of Done

- [x] FastAPI application foundation
- [x] Typed research-plan schemas
- [x] Provider-independent structured LLM interface
- [x] Ollama structured-output provider
- [x] OpenAI-compatible structured-output provider
- [x] Planner prompt with anti-hallucination constraints
- [x] LangGraph `START → planner → END` builder
- [x] Planner API endpoint
- [x] Deterministic unit tests
- [x] Health endpoint

## Features added after Milestone 1

- [x] Search Agent
- [x] Self-hosted SearXNG integration
- [x] Search ranking and deduplication
- [x] Full-page fetching
- [x] SSRF protections
- [x] Evidence extraction
- [x] Evidence grounding validation
- [x] Evidence relevance gate
- [x] Claim consolidation
- [x] Claim-level verification
- [x] Source-leakage protection
- [x] Benchmark verification safeguards
- [x] Coverage analysis
- [x] Coverage-adjusted confidence
- [x] Deterministic final report
- [x] React frontend
- [x] Real LangGraph progress streaming
- [x] Docker deployment
- [x] Container health checks
- [x] Non-root backend container
- [x] Runtime/development dependency separation
- [x] GitHub Actions CI

## Original workflow

~~~text
User Query
    ↓
Planner Agent
    ↓
Structured Research Plan
~~~

## Current workflow

~~~text
User Query
    ↓
Planner
    ↓
Search
    ↓
Ranking / Deduplication
    ↓
Full-page Fetch
    ↓
Evidence Extraction
    ↓
Evidence Relevance Gate
    ↓
Claim Consolidation
    ↓
Verification
    ↓
Coverage Analysis
    ↓
Final Cited Report
~~~
