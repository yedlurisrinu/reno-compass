11# Implementation Plan — Reno Compass Application

This plan outlines the architecture, file layout, dependencies, and verification steps for implementing the complete **Reno Compass** application. The system consists of a FastAPI backend, a premium single-page web UI, deterministic code-level validation tools, GCS session persistence, and a BDD Gherkin test suite.

---

## Architecture Design Principles (12 Dimensions)

We evaluate our proposed system against the 12 key design dimensions:

1.  **Scalability**: Highly scalable stateless FastAPI router. GCS acts as an $O(1)$ key-value session storage engine using session tokens as keys.
2.  **Supportability**: Clear warning notices printed on both PDFs and spreadsheets: *“Confidential: Educational planning artifact only. Not intended for contractor distribution.”* This aligns expectations and prevents liability issues.
3.  **Extendability**: Decoupled, stage-specific agent classes coordinate through a central orchestrator. Allows adding new spaces (e.g., kitchens, landscaping) by implementing a new stage agent class and editing the state transition table.
4.  **Readability**: Adheres strictly to **PEP 8**, **strict type hinting** across the codebase, and **Google-style docstrings** for code clarity.
5.  **Observability**: Integrated FastAPI Logging Middleware captures execution timestamps, tool invocations, active skill contexts, model latency, and token consumption in structured JSON format.
6.  **Maintainability**: No database migrations. Pure object-based persistence simplifies local and cloud configurations.
7.  **Token Cost**: Conversion logs are archived on stage transition, passing only a compact Markdown summary to working memory. This reduces prompt overhead.
8.  **Reducing LLM Hallucination**: Deterministic code-level tools validate allergy compatibility, unit metrics, and structural/electrical envelopes, bypassing LLM generation for safety-critical numbers.
9.  **Modularity**: Decoupled, stage-specific agent classes coordinate through a central orchestrator. Each agent resides in its own isolated module.
10. **Security**: Hashed tokens in logs, strict CORS headers, HttpOnly secure cookies, and environment-isolated service account configurations.
11. **Versioning & Schema Migrations (The 11th Dimension)**: A robust Semantic Versioning (`major.minor.patch`) check is performed on session restore. Major version mismatches reject the reload; minor version mismatches trigger a best-effort load warning.
12. **DRY (Don't Repeat Yourself)**: Avoid redundant files by referencing all runtime reference tables directly from the single source of truth in the `.agents/skills` repository. This eliminates the risk of synchronization issues between local development documentation and production container deployment assets.

---

## DAG Architecture & Stage Coordination

The Reno Compass execution and validation model is structured as a **Directed Acyclic Graph (DAG)**:

```
[Scope Stage] ──► [Design Stage] ──► [Safety Stage] ──► [Logistics Stage] ──► [Materials] ...
     │                 │                  │                   │
     ▼                 ▼                  ▼                   ▼
[Ballpark Calc]   [Layout Calc]    [Envelope Store]    [Displacement Calc]
```

1.  **Stage Dependency DAG**: The 8 stages form a directed path graph: `Scope -> Design -> Safety -> Logistics -> Materials -> Contractor -> DIY -> Synthesis`.
2.  **Cascade Invalidation**: When a restore change is made, the orchestrator traverses the DAG downstream from the modified node. It marks the modified node and all its child nodes (descendants) as `changed_reopened` and nulls their data, leaving parent nodes (ancestors) completely untouched.
3.  **Deterministic Data Flow DAG**: Within each stage, calculations represent data vertices in a sub-DAG (e.g., `Room Dims -> Area/Volume Math -> Lighting fc Target -> Required Fixtures -> Materials Line Items -> Total Cost Rollup`). This ensures strict, one-way propagation of calculated values without circular loops.

---

## Agent, Skill, & Tool Management (Fail-Safe Invariants)

To guarantee high system reliability and reduce Vertex AI invocation failures, the agent execution layer implements the following safety configurations:

*   **Framework Selection**: We use the native **Google Cloud Vertex AI Python SDK** (`google-cloud-aiplatform`) for LLM interactions. This avoids complex third-party abstraction layers (e.g., LangChain) and gives us absolute control over system prompt composition, tool parameters, and token cost tracking.
*   **Wrong Tool/Skill Call Handling**: If the LLM generates a tool call targeting a non-existent tool or passes malformed parameters:
    *   The `BaseAgent` catches the execution error.
    *   It automatically wraps the traceback in a system correction feedback message: *"Error: Tool [name] called with invalid parameters [params]. Please correct and retry."*
    *   It returns this correction message to Gemini as a prompt self-correction loop (limited to 3 attempts). If it still fails, it degrades safely with a `DEGRADED` status.
*   **Token Budget Failure**: If input/output context tokens exceed Vertex limits, the client throws a `RETRYABLE_EXHAUSTED` exception, triggers an automatic context truncation of raw logs (retaining the structured summary), and logs the breach.
*   **Skill Description Overlap**: Dynamic skill loading based on text description can lead to selection ambiguity if descriptions overlap. To resolve this, `src/agents/base.py` enforces a **static skill-routing registry**. Stage keys map to exact lists of permitted skill folder paths, preventing run-time overlap collisions.
*   **Trigger Failure**: If a stage gate fails to evaluate (e.g., Vertex AI times out or does not return a response), the orchestrator blocks the transition. A gate cannot open on a failed check; it flags `gate_not_satisfied` to the client.

---

## User Review & Clarifications Resolved

*   **Session Token Prefix**: Tokens are generated with a recognizable prefix: `reno_s_<random_hex>`.
*   **Web Search Grounding & Curation Fallback Strategy**: 
    *   *For Curated & Code Data*: The model references our frozen database files (RD-1..RD-5) via python tool scripts.
    *   *For Missing Reference Items*: Gemini's native **Google Search Grounding** is used to research the item. The model labels it: *“Estimate based on web search; not from validated project reference data.”*
*   **No Concurrent Locking**: Skipped for simplicity in this single-user interactive UI demo.
*   **Dual base64 Payload**: Complete PDFs and XLSX sheets are generated on Stage 8 final confirmation and returned as base64-encoded strings directly in the JSON response.
*   **Unattended Decisions Logging Protocol**: Logged in `task.md` using `[Major]` or `[Minor]` tags, detailing Scenario, File, and Alternative Approach/Review.

---

## Tech Stack & Library Layer Breakdown

### 1. API Layer
*   `fastapi` (v0.110+): Core web framework.
*   `uvicorn` (v0.28+): ASGI server.
*   `slowapi` (v0.1.9+): Token-bucket rate-limiting middleware.
*   `python-multipart`: For file/PDF upload parsing.

### 2. UI Layer (Frontend HTML/JS/CSS)
*   `HTML5`: Semantic structural layouts.
*   `CSS3 / Vanilla CSS`: Dark-mode styles, responsive flexbox layout, and glassmorphic components.
*   `Vanilla JavaScript (ES6)`: Frontend controller managing chats, cookies, and base64 downloads.
*   `Google Fonts (Inter)`: Premium modern typography.

### 3. Storage & Configuration Layer
*   `google-cloud-storage` (v2.16+): Client library for GCS session storage.
*   `pydantic` (v2.6+): Data validation and settings management.
*   `pydantic-settings` (v2.2+): Configuration parsing via environment variables.

### 4. Model & Logic Layer (LLM Framework)
*   `google-cloud-aiplatform` (v1.44+): Native Google Vertex AI Python SDK.
*   `jinja2` (v3.1+): Hydrating prompt templates with dossier data.

### 5. Tools & Document Generation Layer
*   `fpdf2` (v2.7+): Generating Plan PDF and embedding `dossier.json`.
*   `openpyxl` (v3.1+): Generating shoppable spreadsheets.

### 6. Testing Layer
*   `pytest` (v8.1+): Core unit-testing framework.
*   `pytest-asyncio` (v0.23+): Testing async FastAPI endpoints.
*   `behave` (v1.2.6): BDD Gherkin integration suite.

---

## Phased Execution & Testing Workflow (TDD/BDD Pattern)

We will execute the codebase implementation in 5 sequential, test-alongside-code phases to ensure bugs are isolated early and safety-critical invariants are maintained at every step:

```
[Phase 1: Foundation] ──► [Phase 2: Tools] ──► [Phase 3: Orchestrator] ──► [Phase 4: Agents & Evals] ──► [Phase 5: UI & Deployment]
       │                          │                     │                          │                             │
    Dossier,                   Math,                 State machine,             Gemini client,                 FastAPI,
    Storage,                  Allergies,             Behave Gherkin             LLM prompt evals               Web UI,
    Unit tests                Unit tests             steps (integration)        (LLM-as-a-judge)               Docker / Infra
```

### Phase 1: Foundation & Domain Layer
*   **Source Files**:
    *   `src/config/config.py`: Loads environment configurations, region details, and token TTLs.
    *   `src/domain/dossier.py`: Implements dossier Pydantic models and Semantic Versioning (`SemVer`) check logic.
    *   `src/data/storage.py`: Implements GCS upload/download operations with atomic tmp-write-and-swap logic.
*   **Test Files (Written Alongside)**:
    *   `tests/unit/domain/test_dossier.py`: Tests that invalid field structures fail, and verify major/minor SemVer gating rules.
    *   `tests/unit/data/test_storage.py`: Verifies GCS atomic writes, session token naming conventions (`reno_s_`), and TTL checks using a mocked GCS backend.

### Phase 2: Deterministic Tools
*   **Source Files**:
    *   `src/tools/measurement_math.py`: Calculates areas/volumes; flags implausible coordinates.
    *   `src/tools/envelope_check.py`: Evaluates concrete material selections against stored safety classification envelopes.
    *   `src/tools/allergy_screen.py`: Verifies material parameters against the strict 3-state allergy check.
    *   `src/tools/lighting_calc.py`: Computes footcandle/lumen thresholds per zone.
    *   `src/tools/pdf_xlsx_generator.py`: Renders plan PDFs with embedded JSON attachments and creates shoppable spreadsheets.
*   **Test Files (Written Alongside)**:
    *   `tests/unit/tools/test_measurement_math.py`, `test_envelope_check.py`, `test_allergy_screen.py`, `test_lighting_calc.py`, `test_pdf_xlsx_generator.py`: Verify calculations against all edge cases, verify that unit mismatches throw expected exceptions, and verify that metadata parsing extracts the raw JSON dossier safely from generated PDFs.

### Phase 3: Orchestrator & BDD Steps
*   **Source Files**:
    *   `src/orchestrator.py`: Implements the core runnable state-machine, stage-gate evaluations, and backward transition loops (E1..E4).
*   **Test Files (Written Alongside)**:
    *   `tests/features/steps/steps.py`: Implements the behave step definitions mapping Gherkin features (`tests/features/pipeline.feature`) to the state-machine execution runs. Runs Gherkin validation checks verifying structural cascade reopening, budget loops, and restore confirmations.

### Phase 4: Agents & LLM Safety Evals
*   **Source Files**:
    *   `src/agents/base.py`: Vertex AI client wrapper featuring retry handlers and telemetry loggers.
    *   `src/agents/scope.py` through `synthesis.py`: Stage-specific agent classes containing hydrated prompt structures and references.
*   **Test Files (Written Alongside)**:
    *   `tests/unit/agents/test_base.py`, `test_scope.py`, ..., `test_synthesis.py`: Unit test files mocking Vertex AI API responses.
    *   *LLM Prompt Safety Evaluator*: A testing script that feeds adversarial inputs to agents (e.g. asking for load-bearing DIY cut instructions) and uses an automated LLM-as-a-judge rubric to assert that the Tier-1 firewall remains unbreached.
    *   *Agent & Tool Manager Tests*: Unit tests verifying the base client's response to invalid tool calls (triggering the retry-correction feedback loop), description resolution checks, and token limit triggers.

### Phase 5: FastAPI Endpoints, UI, & Infrastructure
*   **Source Files**:
    *   `src/middleware.py`: Structured logging (excluding SENSITIVE details), correlation ID propagation, and token rate-limiting.
    *   `src/main.py`: Registers routes (`/api/chat`, `/api/session/restore-pdf`, etc.) and serves static client files.
    *   `static/`: Implements premium web interface client (`index.html`, `index.css`, `app.js`).
    *   `infra/`: Holds `Dockerfile`, `docker-compose.yml`, and `setup_gcp.sh`.
*   **Test Files (Written Alongside)**:
    *   `tests/integration/test_endpoints.py`: Verifies endpoints, rate limiter blocks (at 1 request per min), cookie handshakes, and dual base64 downloads.

---

## Verification Plan

### Automated Tests
* We will run pytest to execute unit tests and the behave-driven BDD test suite:
  ```bash
  pytest tests/
  behave tests/features/
  ```

### Manual Verification
* **Local Run**: Launch the application locally:
  ```bash
  docker-compose -f infra/docker-compose.yml up --build
  ```
  Open `http://localhost:8000` in the browser, start a chat session, advance the stage, trigger budget loops, and perform download/restore cycles.
* **PDF Integrity Check**: Open the downloaded PDF in a PDF reader (such as Adobe Acrobat or Chrome PDF viewer) and verify that the layout displays properly. Run a script to extract the embedded `dossier.json` file from the PDF to confirm its extraction integrity.
