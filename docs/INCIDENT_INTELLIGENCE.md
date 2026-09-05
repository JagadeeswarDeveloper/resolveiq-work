# Incident Intelligence

ResolveIQ turns recent complaints into potential business incidents. Automated detection uses careful hypothesis language and never changes an incident to `confirmed`.

## Detection

The detector inspects complaints in a configurable rolling window (`INCIDENT_DETECTION_WINDOW_HOURS`, default 48). It reuses the existing `EmbeddingProvider`, including the deterministic hash fallback when Ollama is unavailable.

A candidate requires:

- the same analyzed category;
- semantic similarity above `INCIDENT_SIMILARITY_THRESHOLD`;
- a shared product or region entity; and
- the same configured time window.

The score is configurable through `INCIDENT_SEMANTIC_WEIGHT`, `INCIDENT_CATEGORY_WEIGHT`, `INCIDENT_CONTEXT_WEIGHT`, and `INCIDENT_TIME_WEIGHT`. Candidates below `INCIDENT_MIN_CLUSTER_SIZE` are ignored. This prevents generic categories such as all delivery complaints from becoming one incident without contextual evidence.

## Anomalies and impact

The MVP records a rolling comparison using the current cluster volume and a conservative baseline. It stores baseline volume, current volume, and percentage change. Impact includes linked customers, high-priority complaints, SLA breaches, affected regions and products, and an explicitly estimated customer-impact amount.

## Lifecycle and auditability

Automation creates or updates `DETECTED` incidents. `INVESTIGATING`, `CONFIRMED`, `MITIGATED`, and `CLOSED` remain business workflow states. Each run persists complaint IDs, scores, signals, thresholds, confidence, and recommended actions in `incident_evidence`, plus an ARC `LEARN` event for each linked complaint.

Detection is idempotent by category and affected region cluster matching, so refresh updates the existing incident instead of creating a duplicate. Evidence rows remain as a history of detection runs.

## Scaling and limitations

The current MVP loads recent complaints and computes top-level pairwise similarity in memory. Production should move embeddings to pgvector, retrieve top-K candidates by index, and run detection asynchronously after complaint creation. The deterministic fallback is useful for demos but is not a semantic model. Entity extraction quality and the simple volume baseline are the primary false-positive and false-negative risks.

## API

- `POST /api/v1/incidents/detect`
- `POST /api/v1/incidents/{id}/refresh`
- `GET /api/v1/incidents/{id}/evidence`
- `GET /api/v1/clusters`
- `GET /api/v1/clusters/{id}`
