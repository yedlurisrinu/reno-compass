# Test Coverage Report

**Suite:** full offline suite — `tests/unit`, `tests/integration`, `tests/e2e`
(run in mock mode: `MOCK_VERTEX_AI=true STORAGE_LOCAL_FALLBACK=true`)
**Result:** 239 passed, 1 skipped
**Total coverage:** **91%** (2418 statements, 225 missed)

Reproduce:

```bash
MOCK_VERTEX_AI=true STORAGE_LOCAL_FALLBACK=true python -m pytest \
  tests/unit tests/integration tests/e2e \
  --cov=src --cov-report=term-missing \
  --cov-report=html:coverage/html --cov-report=xml:coverage/coverage.xml
```

The command above also writes a browsable line-level HTML report to
`coverage/html/index.html` and a machine-readable `coverage/coverage.xml`; both
are generated artifacts and are not checked in (regenerate them anytime with the
command above).

> The `tests/evals/` suite is excluded — it makes live Gemini calls
> (`MOCK_VERTEX_AI=false`) and requires Google credentials. The remaining gaps
> are mostly live-only paths: Vertex/GenAI client init in `agents/base.py`,
> credential/project auto-discovery in `config/config.py`, and the real GCS
> client construction in `data/storage.py`.

| Name                              |    Stmts |     Miss |   Cover |
|---------------------------------- | -------: | -------: | ------: |
| src/agents/\_\_init\_\_.py        |       10 |        0 |    100% |
| src/agents/base.py                |      618 |       80 |     87% |
| src/agents/contractor.py          |        3 |        0 |    100% |
| src/agents/design.py              |        3 |        0 |    100% |
| src/agents/diy.py                 |        3 |        0 |    100% |
| src/agents/logistics.py           |        3 |        0 |    100% |
| src/agents/materials.py           |        3 |        0 |    100% |
| src/agents/safety.py              |        3 |        0 |    100% |
| src/agents/scope.py               |        3 |        0 |    100% |
| src/agents/synthesis.py           |        3 |        0 |    100% |
| src/config/\_\_init\_\_.py        |        2 |        0 |    100% |
| src/config/config.py              |      100 |       26 |     74% |
| src/data/\_\_init\_\_.py          |        2 |        0 |    100% |
| src/data/storage.py               |      121 |        9 |     93% |
| src/domain/\_\_init\_\_.py        |        2 |        0 |    100% |
| src/domain/dossier.py             |      319 |        2 |     99% |
| src/main.py                       |      511 |       60 |     88% |
| src/middleware.py                 |       59 |        8 |     86% |
| src/orchestrator.py               |      264 |       39 |     85% |
| src/tools/\_\_init\_\_.py         |        7 |        0 |    100% |
| src/tools/allergy\_screen.py      |       22 |        0 |    100% |
| src/tools/envelope\_check.py      |       65 |        0 |    100% |
| src/tools/lighting\_calc.py       |       26 |        0 |    100% |
| src/tools/measurement\_math.py    |       51 |        0 |    100% |
| src/tools/pdf\_xlsx\_generator.py |      181 |        0 |    100% |
| src/tools/pricing\_ballpark.py    |       34 |        1 |     97% |
| **TOTAL**                         | **2418** |  **225** | **91%** |
