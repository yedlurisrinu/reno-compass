# Implementation Plan — Auto-Advancement & Clean Client Payloads

This plan implements:
1. **Send Button Relocation (1A)**: Moving the Send button to its own actions row below the textarea. Removing the header Approve & Advance button.
2. **Customer Parameter Role Filtering (2A)**: Isolating user messages for stated parameter extraction, separating them from agent explanations.
3. **Flat Response Payload (3A)**: Removing the `"dossier"` response envelope and flattening payload properties.
4. **Backend-Driven Auto-Advance (4A)**: Catching the `[APPROVE_STAGE_TRANSITION]` token inline, triggering stage transitions, and launching the next stage coordinator.

---

## User Review Required
> [!IMPORTANT]
> * **Auto-Advance Token**: The model will append `[APPROVE_STAGE_TRANSITION]` when ready to advance. The server intercepts this, advances the pipeline, and immediately seeds the *next* stage's welcome prompt into the response feed.
> * **No More "Dossier" in UI Responses**: The JSON responses from the server will no longer expose the `"dossier"` key. Flat fields (`current_stage`, `conversation`) will be returned, and `app.js` is updated to read them directly.

---

## Proposed Changes

### 1. Style & HTML Layout

#### [MODIFY] [index.html](file:///home/yedlurisrinu/0-github/reno-compass/static/index.html)
* Remove the **Approve & Advance** button from the header panel.
* Restructure the chat input bar:
  ```html
  <div class="chat-input-bar">
      <textarea id="chatInput" placeholder="Type your message here... (Shift+Enter to send)"></textarea>
      <div class="chat-actions-row">
          <button id="sendBtn">Send</button>
      </div>
  </div>
  ```

#### [MODIFY] [index.css](file:///home/yedlurisrinu/0-github/reno-compass/static/index.css)
* Update `.chat-input-bar` to layout elements vertically (`flex-direction: column`).
* Style `.chat-actions-row` to align the Send button to the bottom right.

---

### 2. Frontend Interface (UI)

#### [MODIFY] [app.js](file:///home/yedlurisrinu/0-github/reno-compass/static/app.js)
* Refactor response handlers to process flat properties (`current_stage`, `conversation`) directly, removing all `data.dossier` accesses.
* Update button click handler references.

---

### 3. Backend Agent & Pipeline Layer

#### [MODIFY] [behavior.md](file:///home/yedlurisrinu/0-github/reno-compass/.agents/rules/behavior.md)
* Append the instruction: *"When all stage requirements are fully resolved and the customer is ready to advance, append the special marker `[APPROVE_STAGE_TRANSITION]` at the very end of your final response text."*

#### [MODIFY] [base.py](file:///home/yedlurisrinu/0-github/reno-compass/src/agents/base.py)
* Update `extract_and_update_stage_dossier()`:
  * Filter turns list: `user_text` compiles only turns with `role="user"`. `agent_text` compiles only turns with `role="agent"`.
  * Pass `user_text` to the schema extraction pass for stated parameters (target budgets, zipcodes).
  * Use agent logic or `agent_text` for ballpark estimates.

#### [MODIFY] [main.py](file:///home/yedlurisrinu/0-github/reno-compass/src/main.py)
* Update `get_client_safe_state()` to return a flat dict:
  ```python
  return {
      "current_stage": current_stage,
      "conversation": conversation
  }
  ```
* Update `/api/chat` route logic:
  * Check if the generated `agent_response` contains `[APPROVE_STAGE_TRANSITION]`.
  * If it does:
    1. Strip the tag from the text response.
    2. Set `stage_obj.user_final_verdict = True`.
    3. Call `advance_pipeline(dossier)`.
    4. Save the dossier.
    5. Resolve the *next* stage agent, fetch its initial questions, and append that starter turn to the next stage's conversation history.
* Remove the `/api/session/advance` route from `main.py` since transitions are now inline.

---

## Verification Plan

### Automated Tests
* Run the test suite:
  ```bash
  PYTHONPATH=.:src pytest tests/
  ```
