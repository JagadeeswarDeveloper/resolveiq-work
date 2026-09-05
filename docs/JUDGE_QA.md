# Judge Q&A

## Why AI?
AI handles semantic classification, sentiment, summarization, grounded recommendation, and similarity analysis. Deterministic services retain control of priority, policy gates, status changes, and external actions.

## Why multiple agents?
The three agents have narrow contracts: UnderstandingAgent interprets, ResolutionAgent recommends from retrieved evidence, and SupervisorAgent routes risk. This makes inputs, outputs, guardrails, and failures inspectable.

## What makes it agentic?
A persisted workflow state advances through conditional nodes, calls tools, pauses for approval, resumes from a checkpoint, and records auditable events. It is not a chat-only response.

## How is safety handled?
LLM output is schema-validated. Legal, fraud, safety, and regulatory signals escalate. Missing policy evidence, high compensation, and human-review flags require approval. Enterprise actions are currently mock handlers.

## What happens if Ollama is unavailable?
The provider abstraction falls back to the deterministic provider in demo mode. Live Ollama integration is opt-in tested and remains environment-dependent.

## How is priority calculated?
Priority is deterministic from sentiment, severity, repeat history, customer tier, and related business signals. The model does not directly set the final status.

## How are incidents detected?
The existing Phase 4 service combines semantic, category, context, time-window, and volume signals. It is idempotent and links supporting evidence.

## How is success measured?
The evaluation dataset defines expected understanding, priority, policy, incident, and routing outcomes. The runner intentionally leaves model metrics empty until predictions are collected.

## What is implemented versus future?
Implemented: FastAPI, SQLite/PostgreSQL-compatible schema, three agents, fallback/Ollama abstraction, RAG, incident detection, persisted orchestration, approval pause/resume, ARC events, and deterministic demo routing. Prototype: mock business actions, evaluation prediction collection, and the technical observability view. Future: authenticated reviewers, real CRM/helpdesk actions, adjudicated evaluation labels, and production-scale queues.

## Why not ChatGPT or existing support software?
ResolveIQ is a controlled decision workflow around complaint intelligence, policy evidence, incident signals, and auditability. It complements ticket systems rather than pretending to replace their operational integrations.
