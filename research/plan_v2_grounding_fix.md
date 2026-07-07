# Implementation Plan — Google AI Studio & Vertex AI Tool Schema Bifurcation

This plan resolves the tool declaration mismatch between the legacy Google AI Studio SDK and the Vertex AI gRPC client.

## User Review Required
> [!IMPORTANT]
> * **Google AI Studio (`genai.GenerativeModel`)** only supports `google_search_retrieval`.
> * **Vertex AI (`GenerativeModel`)** only supports `google_search`.
> * We will configure the tool schema dynamically based on the active client.

---

## Proposed Changes

### Backend Agent Layer

#### [MODIFY] [base.py](src/agents/base.py)
* Update `execute_vertex_call()`:
  * In the **Google AI Studio** client block, set the grounding tool config to `{"google_search_retrieval": {}}`.
  * In the **Vertex AI** (`_execute_vertex_api_call`) client block, set the grounding tool config to `Tool.from_dict({"google_search": {}})` (which we verified successfully builds the new `google_search` schema object).

---

## Verification Plan

### Automated Tests
* Run unit and integration tests:
  ```bash
  PYTHONPATH=.:src pytest tests/
  ```
