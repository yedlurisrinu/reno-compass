# Walkthrough — UI Design Layout, Conversation & API Grounding Improvements

We restructured the Reno Compass web interface, updated the core agent behavior models to align with clean visual guidelines, resolved session caching/cookie issues, and corrected Google Cloud Vertex AI & Google AI Studio search grounding errors.

---

## 1. UI Redesign & Tagline Updates

### Layout Restructuring
* **Files modified**: [index.html](../static/index.html) and [index.css](../static/index.css)
* **Changes**:
  * Removed the entire **Session Dossier Viewer** panel so that the raw database structures are not exposed to the user.
  * Reconfigured the grid layout of `.app-layout` to `grid-template-columns: 1fr` (single column), expanding the chat window to occupy the entire width of the page.
  * Moved the **Restore PDF**, **Approve & Advance** and **Download Blueprint Package** action buttons to the chat panel header.
  * Removed the redundant **Reset** button from the header.
  * Added styling for disabled states on the action buttons (`opacity: 0.45` and `cursor: not-allowed`).

### Tagline Modification
* **File modified**: [index.html](../static/index.html)
* **Change**: Changed the application tagline to: `"Home re-imagine - A path to realize emphatically"`.

### Screen Responsiveness Overrides
* **File modified**: [index.css](../static/index.css)
* **Logic implemented**: Appended mobile and tablet `@media` screen breakpoints (under 1100px and 768px):
  * Steps tracker adjusts text size and scrolls horizontally rather than squishing or clipping.
  * Header layout stacks logo/title and step indicator elements cleanly to avoid overlap.
  * Layout container padding decreases dynamically to maximize chat view area.
  * Panel headers adapt layouts on handheld devices.

### Newline Rendering Fix
* **File modified**: [index.css](../static/index.css)
* **Logic implemented**: Added `white-space: pre-wrap;` to the `.chat-message` selector class. This tells the browser's CSS parser to respect and render all literal newline characters (`\n`) and double newlines (`\n\n`) output by the model, rather than collapsing them.

### UI Textarea Height & Send Button Layout
* **Files modified**: [index.html](../static/index.html), [index.css](../static/index.css)
* **Logic implemented**:
  * Moved the **Send** button into its own row (`.chat-actions-row`) underneath the `#chatInput` textarea to avoid vertically stretching the button.
  * Increased the chat input height to `min-height: 100px` for optimal typing comfort.

### Shift+Enter Key Submission Trigger
* **File modified**: [app.js](../static/app.js)
* **Logic implemented**: Refactored the keydown listener on the chat input box. Pressing a standard **Enter** key now inserts normal new lines inside the textarea to type paragraphs naturally, while pressing **Shift + Enter** triggers message submission.

---

## 2. Dynamic Elicitation & Welcome Duplication Fix

### Elicitation Startup
* **File modified**: [index.html](../static/index.html)
  * Removed the hardcoded welcome message. The conversation starts completely clean.
* **File modified**: [app.js](../static/app.js)
  * Implemented `fetchInitialQuestions()` which automatically sends an invisible starter query to the backend agent upon initializing a fresh session.
  * Implemented `renderConversationHistory(state)` to automatically rebuild and populate the chat feed when resuming an active session.

### Conversation Turn Persistence
* **File modified**: [main.py](../src/main.py)
  * Updated the `/api/chat` route to construct and append `ConversationTurn` objects to the active stage's `conversation` list within the dossier.

---

## 3. Cache Prevention & Incognito Persistence

### Caching Prevention
* **File modified**: [middleware.py](../src/middleware.py)
* **Logic implemented**: Added headers directly inside the `TelemetryLoggingMiddleware` to intercept requests for the landing page (`/`) and static folder assets (`/static/*`), injecting caching prevention headers.

### Incognito Session Restore & Cookie Fixes
* **File modified**: [main.py](../src/main.py)
  * Implemented `@app.post("/api/session/load")` to allow loading a session dossier dynamically from local storage or GCS cache.
  * Removed any `secure=True` cookie declarations.
* **File modified**: [app.js](../static/app.js)
  * Persists the active session token to browser `localStorage` under `reno_active_token`.

### Client Safe State Serialization (Flat Response Payload)
* **File modified**: [main.py](../src/main.py)
  * Updated `get_client_safe_state(dossier: Dossier) -> dict` to return a flattened response payload containing `current_stage` and `conversation` at the top level of the JSON response, removing `"dossier"` key prefixes completely.
* **File modified**: [app.js](../static/app.js)
  * Refactored JavaScript rendering, load handles, and chat responses to bind to `current_stage` and `conversation` at the top level.

---

## 4. Extraction & Validation Updates

### Stated Parameters User-Only Filtering
* **File modified**: [base.py](../src/agents/base.py)
  * Updated `extract_and_update_stage_dossier()`: Isolates conversation logs by role. Stated preferences (like target budgets, zip codes, and goals) are extracted strictly from turns where `role == "user"`.
  * Added instructions to the `_run_live_extraction` prompt and passed `user_text` as a dedicated input so the model does not extract explanatory ballpark values.

### Default Value Resets & Budget Validation
* **File modified**: [base.py](../src/agents/base.py)
  * Updated `_create_default_stage_object()`: Sets default numerical fields to `-1.0` (or `"-1"` for strings like zipcode).
  * Updated extraction logic: If a valid `budget_target` is provided by the customer but the `budget_ceiling` remains uninitialized, the system matches `budget_ceiling = budget_target`.
* **File modified**: [orchestrator.py](../src/orchestrator.py)
  * Refactored `evaluate_stage_gate()` for the `"scope"` stage: Blocks advancement if `scope.budget_target <= 0.0` or `scope.budget_target == -1.0`.

---

## 5. Inline Stage Advancement (No Approve Button)

* **File modified**: [index.html](../static/index.html)
  * Removed the header "Approve & Advance" button completely.
* **File modified**: [app.js](../static/app.js)
  * Cleaned out all event listeners and visibility logic associated with `btnAdvance`.
* **File modified**: [behavior.md](../.agents/rules/behavior.md)
  * Appended the instruction: *"When all stage requirements are fully resolved and the customer is ready to advance, append the special marker `[APPROVE_STAGE_TRANSITION]` at the very end of your final response text."*
* **File modified**: [main.py](../src/main.py)
  * Implemented an auto-advancement interceptor in the `/api/chat` endpoint:
    1. Checks if `agent_response` contains `[APPROVE_STAGE_TRANSITION]`.
    2. If present, strips the tag from the text (so the user never sees it).
    3. Sets `stage_obj.user_final_verdict = True`.
    4. Automatically invokes `advance_pipeline(dossier)`.
    5. Saves the advanced session.
    6. Triggers the next stage agent's welcome greeting and initial questions, appending them to the next stage conversation and combining it with the response text.

---

## 6. Google Search Grounding Tool Resolution (Vertex AI & AI Studio)

* **File modified**: [base.py](../src/agents/base.py)
* **Change**:
  * Corrected the search grounding tool configuration for both **Google AI Studio** and **Google Cloud Vertex AI** client model invocations.
  * In `_execute_vertex_api_call()` (Vertex AI gRPC client), replaced the deprecated `Tool.from_google_search_retrieval(grounding.GoogleSearchRetrieval())` constructor with `Tool.from_dict({"google_search": {}})`.
  * In `execute_vertex_call()` (Google AI Studio REST client), configured `tools.append("google_search_retrieval")` instead of the unsupported string `"google_search"` or dictionary.
  * This aligns both clients with their respective supported search grounding API parameter schemas, eliminating tool formatting validation errors.

---

## 7. Storage Fallback & Mock Schema Bug Fixes (New Discoveries)

* **File modified**: [storage.py](../src/data/storage.py)
  * Updated `read_session()`: Caught a bug where GCS throwing `NotFound` on a missing bucket bypassed the local disk cache fallback block. Now, a `NotFound` exception still checks the local storage cache directory first (in case it was saved locally during a GCS upload failure) before returning `None`.
* **File modified**: [base.py](../src/agents/base.py)
  * Updated `_run_mock_extraction()`: Corrected the mock initializations for `RefinedEstimate`, `DesignOption`, `ChosenDesign`, `TierClassification`, `MaterialLineItem`, `MaterialTotal`, `CoverageCheckItem`, and `DiyProcedure`. These mock models were using outdated constructors that crashed stage transitions in mock test environments.
  * Fixed a mock zipcode regex collision where 5-digit target budgets were incorrectly parsed as property zipcodes.

---

## 8. Live Evaluation & Integration Test Results

We established a new evaluations test suite under `tests/evals/` containing 6 test files to prevent regressions on API key tool validation, payload exposure, extraction parameters, stage transitions, and GCS fallback checks.

* Run the full test suite (including unit tests and the evaluations suite):
  ```bash
  PYTHONPATH=.:src pytest
  ```
* **Result**: **All 46 tests passed successfully.**
  ```text
  ======================= 46 passed, 72 warnings in 8.98s ========================
  ```
