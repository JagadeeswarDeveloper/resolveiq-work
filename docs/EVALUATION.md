# ResolveIQ Evaluation

## Dataset

`data/evaluation/cases.json` contains 50 isolated ground-truth complaints. It is separate from demo seed data and covers account, billing, delivery, refund, product quality, fraud, safety, legal, and compliance cases across all three routing paths.

Distribution: 20 `AUTO_RESOLVE`, 15 `HUMAN_APPROVAL`, and 15 `ESCALATE`.

## Runner

Run:

```powershell
$env:PYTHONPATH = "backend"
c:/Users/conta/projects/resolveIQ/.venv/Scripts/python.exe -m app.evaluation.runner
```

The runner validates dataset completeness and provides metric helpers for accuracy. It reports `null` for model-dependent metrics until predictions are supplied; the project does not claim accuracy from labels alone.

## Metrics

The planned evaluation measures understanding category, intent, sentiment, urgency, and entities; deterministic priority agreement; RAG top-k hit rate and evidence coverage; resolution validity, grounding, action correctness, hallucination rate, and calibration; and incident precision, recall, and false-positive rate.

Current dataset integrity result: 50/50 records complete. Model prediction metrics: not yet measured.

## Limitations

The current runner is a ground-truth harness, not a fabricated benchmark. A production evaluation job should persist predictions, provider/model versions, retrieved chunks, and latency per case, then calculate the metrics above by dataset split. The incident labels are controlled expectations and should be expanded with adjudicated operational data before production decisions.
