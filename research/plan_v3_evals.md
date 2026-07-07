# Implementation Plan — Live Evaluation & Integration Test Suite
This plan establishes a dedicated Live Eval & Integration Test framework under `tests/evals/` to verify SDK client behaviors, parameter extraction accuracy, and stage auto-advancement transitions against actual model calls.

---

## User Review Required
> [!IMPORTANT]
> * **Live API Credentials**: These tests run with `MOCK_VERTEX_AI=false`. They execute actual model calls (charging token usage and requiring active credentials) and are isolated under `tests/evals/` to be run selectively (e.g., `pytest tests/evals/`).
> * **Zero-Regression Evals**: We will map out specific eval scenarios to cover the 5 major issues we've encountered so far.
---

## Proposed Test Scenarios & Evals

### 1. SDK Model & Tool Initialization Eval (`test_tool_compilation.py`)
* **Goal**: Prevent gRPC `INVALID_ARGUMENT` (Vertex AI) and `ValueError` (AI Studio) tool config schema crashes.
* **Mechanism**: Programmatically instantiate the `GenerativeModel` client wrappers for both Vertex AI and AI Studio with search grounding enabled and verify the SDK parses the tool lists successfully.

### 2. Client Safe State Filter Eval (`test_payload_exposure.py`)
* **Goal**: Guarantee that no database structures or private dossier fields are exposed to the client.
* **Mechanism**: Call the session endpoints and assert that responses strictly contain flat fields (`current_stage`, `conversation`) and do not expose keys like `"dossier"`, `"envelope"`, or sub-objects.

### 3. Customer Parameter Extraction Accuracy Eval (`test_extraction_accuracy.py`)
* **Goal**: Prevent the extractor from mistaking the agent's ballpark explanation numbers for the user's stated choices.
* **Mechanism**:
  * Seed a conversation log where the Agent says *"A standard ballpark estimate is $18,000 to $22,000"* and the User says *"My budget is $15,000"*.
  * Run the extraction and assert: `stage_obj.budget_target == 15000.0` (extracting strictly from user turns).

### 4. Inline Stage Auto-Advancement Eval (`test_auto_advance_transition.py`)
* **Goal**: Validate that the backend intercepts the inline completion token and transitions the pipeline stage cleanly.
* **Mechanism**: 
  * Mock a final agent response ending with `[APPROVE_STAGE_TRANSITION]`.
  * Trigger `/api/chat` and assert:
    * The stage in the returned payload changes from `"scope"` to `"design"`.
    * The `[APPROVE_STAGE_TRANSITION]` tag is stripped from the returned text.
    * The starting questions for the `"design"` stage are automatically appended to the conversation feed.

### 5. Storage Fallback Resiliency Eval (`test_storage_resiliency.py`)
* **Goal**: Verify GCS-to-local caching fallback logic operates without returning 500 errors.
* **Mechanism**: Temprorarily poison/blank the bucket configurations and verify that session loads/writes fall back to local disk caches gracefully.

---

## Proposed Changes

### [NEW] [test_tool_compilation.py](tests/evals/test_tool_compilation.py)
* Test suite targeting `execute_vertex_call` tools array structures.

### [NEW] [test_extraction_accuracy.py](tests/evals/test_extraction_accuracy.py)
* Test suite for role-filtered extraction passes.

### [NEW] [test_auto_advance_transition.py](tests/evals/test_auto_advance_transition.py)
* Test suite checking regex matches for the transition token and stage state changes.

### [NEW] [test_storage_resiliency.py](tests/evals/test_storage_resiliency.py)
* Test suite verifying offline local storage fallback.

---

## Verification Plan

### Automated Evals Execution
* Run only the live evaluations suite:
  ```bash
  PYTHONPATH=.:src pytest tests/evals/
  ```
