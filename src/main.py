"""Main entrypoint for the Reno Compass FastAPI backend application."""

import json
import logging
import logging.config
import os
import re
import secrets
from datetime import datetime

from fastapi import Cookie, FastAPI, File, HTTPException, Response, UploadFile
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from config.config import settings
from data.storage import delete_session, read_session, write_session
from domain.dossier import Dossier, DossierEnvelope, ProjectBody

# Resolve log file path with fallback
LOG_DIR = "/app/logs"
LOG_FILE = os.path.join(LOG_DIR, "reno-compass.log")
try:
    os.makedirs(LOG_DIR, exist_ok=True)
    # Test file writability
    test_path = os.path.join(LOG_DIR, ".write_test")
    with open(test_path, "w") as f:
        f.write("test")
    os.remove(test_path)
except Exception:
    # Fallback to local logs directory in the project workspace
    LOG_DIR = os.path.abspath("logs")
    LOG_FILE = os.path.join(LOG_DIR, "reno-compass.log")
    os.makedirs(LOG_DIR, exist_ok=True)

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {"standard": {"format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"}},
    "handlers": {
        "console": {"class": "logging.StreamHandler", "formatter": "standard", "level": "DEBUG"},
        "file": {
            "class": "logging.FileHandler",
            "filename": LOG_FILE,
            "formatter": "standard",
            "level": "DEBUG",
        },
    },
    "root": {"handlers": ["console", "file"], "level": "DEBUG"},
    "loggers": {
        "reno_project": {"handlers": ["console", "file"], "level": "DEBUG", "propagate": False}
    },
}

logging.config.dictConfig(LOGGING_CONFIG)
logger = logging.getLogger("reno_project")

from agents import (
    ContractorAgent,
    DesignAgent,
    DiyAgent,
    LogisticsAgent,
    MaterialsAgent,
    SafetyAgent,
    ScopeAgent,
    SynthesisAgent,
)
from middleware import TelemetryLoggingMiddleware
from orchestrator import (
    advance_pipeline,
    diy_eligible_items,
    evaluate_stage_gate,
    reopen_stage_and_cascade,
)
from tools.pdf_xlsx_generator import (
    extract_dossier_json_from_pdf,
    generate_dossier_pdf,
    generate_materials_xlsx,
)

# Stage-specific hint shown when auto-advance is blocked because a stage gate is
# not yet satisfied. Keeps the user message accurate per stage (the scope gate
# needs budget/zip; later stages need very different things).
# The inline stage-transition control tag, bracketed or bare — detected for
# advancement, then stripped so it never reaches the customer.
_TRANSITION_TAG_RE = re.compile(r"\[?\s*APPROVE_STAGE_TRANSITION\s*\]?", re.IGNORECASE)

# Explicit, deterministic proceed-intent in the USER's own message. Precise on
# purpose: loose approvals ("looks good", "sounds good") do NOT match on their own,
# so merely discussing a later stage never advances the pipeline — only a clear
# request to move on does. The substantive stage gate still guards the actual jump.
_PROCEED_INTENT_RE = re.compile(
    r"\b("
    r"proceed|move on|move forward|move to the next|next stage|next step|go ahead|"
    r"finali[sz]e|lock it in|wrap it up|"
    r"let'?s (go|move|proceed|continue|finali[sz]e|do it)|"
    r"ready to (proceed|move|continue|finali[sz]e)|"
    r"i'?m ready|we'?re ready|i'?m done|that'?s all i need"
    r")\b",
    re.IGNORECASE,
)


def _is_proceed_intent(message: str | None) -> bool:
    """True when the user's message is an explicit request to advance the pipeline."""
    return bool(message and _PROCEED_INTENT_RE.search(message))


# A short, whole-message affirmation ("yes", "ok", "sounds good", "looks good"). This
# is a WEAKER signal than proceed-intent: on its own it never advances — it only counts
# as a confirmation when the caller has already established that the stage is AT its
# decision boundary (every requirement met bar the go-ahead). That guard is what stops a
# stray "yes" mid-Q&A ("yes, I have a dog") from jumping the pipeline. Matched only when
# the ENTIRE message is the affirmation (optionally with the confirm chip's own wording),
# so "yes, but change the tub" — which carries a follow-up request — does NOT match.
_AFFIRMATION_RE = re.compile(
    r"^\s*(?:"
    r"yes|yep|yeah|yup|ya|ok|okay|k|sure|"
    r"correct|right|agreed?|confirm(?:ed)?|approved?|"
    r"sounds?\s+good|looks?\s+good|looks?\s+right|that'?s?\s+(?:right|correct|good|it)|"
    r"perfect|great|fine|good|done|"
    r"yes,?\s+proceed|finali[sz]e\s+my\s+plan"
    r")\s*[.!]*\s*$",
    re.IGNORECASE,
)


def _is_affirmation(message: str | None) -> bool:
    """True when the whole message is a bare affirmation (see ``_AFFIRMATION_RE``)."""
    return bool(message and _AFFIRMATION_RE.match(message))


# One-tap chip labels for the DIY/Contractor decision flow. The text doubles as the
# user message when clicked, so the deterministic mappers below key off these exact
# strings (plus a few natural-language variants) to record the decision server-side.
_CONTRACTOR_DIY_YES = "I'll do the eligible work myself"
_CONTRACTOR_DIY_NO = "Use contractors for everything"
_DIY_ITEM_CAN = "I can do this one myself"
_DIY_ITEM_CANT = "I can't — assign this to a professional"

# Input-box hint shown while a DIY item is under discussion — the decision chips are
# the two commitments, but questions are free-form: the user just types them. Replaces
# a dedicated "I have a question" chip (which forced a needless click → "what's your
# question?" round-trip) with a plain invitation to type.
_DIY_ITEM_INPUT_HINT = (
    "Pick an option above — or if you have a question about this task, "
    "just type it here and I'll answer before you decide."
)

# Input-box hint shown at a standard stage's decision boundary, alongside the single
# "Yes, proceed" chip. Replaces the old "Not yet — I'd like to change something" chip:
# changing something is free-form, so the user just types it.
_CONFIRM_INPUT_HINT = (
    "If everything looks right, hit “Yes, proceed.” "
    "If you'd like to change anything first, just tell me here."
)


def _stage_ready_to_confirm(dossier: Dossier, stage: str) -> bool:
    """Whether ``stage`` has met every requirement except the user's final confirmation.

    This is the "decision boundary": all of the stage's data/topics are captured and
    the only thing left is the family's go-ahead. We compute it by asking the real
    stage gate whether it WOULD pass if the verdict were given — temporarily, without
    persisting — so the proceed chip appears only when a confirmation actually makes
    sense, never during the earlier question-and-answer turns.
    """
    stage_obj = getattr(dossier.project, stage, None)
    if stage_obj is None or not hasattr(stage_obj, "user_final_verdict"):
        return False
    original = stage_obj.user_final_verdict
    stage_obj.user_final_verdict = True
    try:
        return evaluate_stage_gate(dossier, stage)
    finally:
        stage_obj.user_final_verdict = original


def _quick_replies_for(dossier: Dossier) -> list[str]:
    """Clickable one-tap replies offered under the agent's message.

    Chips appear only at genuine decision points, never during ordinary Q&A:
      * Contractor — the all-or-none DIY intent choice, while eligible work exists.
      * DIY — the two per-item commitments (can-do / hand-off), while an item is on
        the table; questions are typed freely, not chipped.
      * Any standard stage — a single "Yes, proceed" chip, but ONLY once the stage has
        met every requirement bar the final go-ahead (the decision boundary). Changing
        something is free-form (typed), so there is no "change" chip.
    The confirm chip's text is deliberate proceed-intent wording so a click flows
    through the same deterministic advancement path as typing it.
    """
    current_stage = dossier.envelope.current_stage
    if current_stage == "complete":
        return []

    # Contractor: all-or-none DIY intent, asked only while eligible work exists and
    # the choice has not yet been recorded.
    if current_stage == "contractor_validation" and diy_eligible_items(dossier):
        cv = dossier.project.contractor_validation
        if cv is None or cv.wants_diy is None:
            return [_CONTRACTOR_DIY_YES, _CONTRACTOR_DIY_NO]

    # DIY: the two per-item commitments while an item is still on the table. Questions
    # are not a chip — the user types them (see _DIY_ITEM_INPUT_HINT).
    if current_stage == "diy_planning":
        diy = dossier.project.diy_planning
        if diy is not None and diy.active_item:
            return [_DIY_ITEM_CAN, _DIY_ITEM_CANT]

    # Standard stages: offer the proceed chip ONLY at the decision boundary.
    if _stage_ready_to_confirm(dossier, current_stage):
        confirm = "Finalize my plan" if current_stage == "synthesis" else "Yes, proceed"
        return [confirm]

    return []


def _input_hint_for(dossier: Dossier) -> str | None:
    """Optional placeholder hint for the chat input box, by stage state.

    Returns the DIY per-item invitation to type a question while an item is under
    discussion, or the type-to-change invitation at a decision boundary; None
    otherwise (the client keeps its default placeholder).
    """
    current_stage = dossier.envelope.current_stage
    if current_stage == "complete":
        return None
    if current_stage == "diy_planning":
        diy = dossier.project.diy_planning
        if diy is not None and diy.active_item:
            return _DIY_ITEM_INPUT_HINT
        # No active item -> all items decided; fall through to the confirm-boundary hint.
    if _stage_ready_to_confirm(dossier, current_stage):
        return _CONFIRM_INPUT_HINT
    return None


# Natural-language matchers for the decision chips (also catch a typed equivalent).
_CONTRACTOR_DIY_NO_RE = re.compile(
    r"contractors?\s+for\s+everything|use\s+contractors|no\s+diy|hire\s+(a\s+)?(pro|contractor)",
    re.IGNORECASE,
)
_CONTRACTOR_DIY_YES_RE = re.compile(
    r"eligible\s+work\s+myself|do\s+(the\s+work|it|them)\s+myself|i'?ll\s+diy|want\s+to\s+diy",
    re.IGNORECASE,
)
_DIY_CANT_RE = re.compile(
    r"can'?t|cannot|assign\s+.*profession|use\s+a\s+profession|hand\s+(this|it)\s+off|"
    r"hire\s+(a\s+)?(pro|contractor)",
    re.IGNORECASE,
)
_DIY_REFINE_RE = re.compile(
    r"question|refine|clarif|not\s+sure|tell\s+me\s+more|what\s+about|enhance",
    re.IGNORECASE,
)
_DIY_CAN_RE = re.compile(
    r"can\s+do\s+this|do\s+this\s+(one\s+)?myself|i'?ll\s+do\s+this|i\s+can\s+handle",
    re.IGNORECASE,
)


def _apply_contractor_diy_choice(dossier: Dossier, message: str | None) -> bool:
    """Records the all-or-none DIY intent at the Contractor stage.

    Returns True when the message expressed a DIY-intent choice (either chip or a
    typed equivalent), having set ``contractor_validation.wants_diy`` accordingly.
    A True result is treated by the caller as an explicit proceed signal, since the
    choice routes the pipeline (wants_diy=False skips DIY straight to synthesis).
    """
    if dossier.envelope.current_stage != "contractor_validation" or not message:
        return False
    if not diy_eligible_items(dossier):
        return False
    cv = dossier.project.contractor_validation
    if cv is None:
        return False
    # Check the opt-out first: "no DIY / contractors for everything" is the more
    # specific intent and must not be shadowed by a generic "do it" match.
    if _CONTRACTOR_DIY_NO_RE.search(message):
        cv.wants_diy = False
        return True
    if _CONTRACTOR_DIY_YES_RE.search(message):
        cv.wants_diy = True
        return True
    return False


def _apply_diy_item_decision(dossier: Dossier, message: str | None) -> str | None:
    """Records the per-item DIY decision on the item currently under discussion.

    Applied BEFORE the agent runs so that, once an item is decided, the seeding pass
    advances ``active_item`` and the agent presents the next item. Returns:
      * "decided" — user_feasible was set (can-do=True, or opt-out=False + reclassify)
      * "refine"  — a question/refinement pass (refine_count bumped, no decision)
      * None       — the message wasn't a per-item decision.
    An atomic, whole-item decision (no partial hand-off within one Safety item).
    """
    if dossier.envelope.current_stage != "diy_planning" or not message:
        return None
    diy = dossier.project.diy_planning
    if diy is None or not diy.procedures:
        return None
    # The item on the table is the first still-pending one (mirrors the seeding pass).
    order = diy_eligible_items(dossier)
    pending = [p for p in diy.procedures if p.item in order and p.user_feasible is None]
    if not pending:
        return None
    pending.sort(key=lambda p: order.index(p.item))
    active = pending[0]

    # A genuine question (now typed freely instead of chipped) is NEVER a decision,
    # even if it contains words like "can" or "can't" ("Can I do this without a
    # permit?"). Treat any question mark as a refine pass: answer it, don't commit.
    if "?" in message:
        active.refine_count += 1
        return "refine"

    # Opt-out ("can't") is checked before "can" so a message like "I can't do this"
    # is never misread as a can-do by the looser can-do matcher.
    if _DIY_CANT_RE.search(message):
        active.user_feasible = False
        active.reclassify_to_professional = True
        return "decided"
    if _DIY_REFINE_RE.search(message):
        active.refine_count += 1
        return "refine"
    if _DIY_CAN_RE.search(message):
        active.user_feasible = True
        active.reclassify_to_professional = False
        return "decided"
    return None


_STAGE_BLOCK_HINTS = {
    "scope": "your budget, zip code, and project goals",
    "design": "your chosen design option",
    "safety_permit": "your consent to the professional-work notes and any permits",
    "logistics_feasibility": "whether you'll stay in the home during the remodel",
    "materials": "your material selections",
    "contractor_validation": "the contractor advisory checklist",
    "diy_planning": "the DIY task steps for the work you'll do yourself",
    "synthesis": "your final go-ahead on the plan",
}


def _gate_missing_reasons(dossier: Dossier, stage: str) -> list[str]:
    """Plain-language list of the SPECIFIC requirements still unmet for ``stage``.

    Mirrors ``evaluate_stage_gate`` minus the final-verdict check, so it explains
    exactly WHY an advance is blocked. Without this, the block warning names generic
    fields (e.g. "budget, zip code, and project goals") the user has already given,
    while the real blocker (often an unanswered allergy question, or missing size) goes
    unnamed — and the conversation loops as they re-send what was never missing.
    """
    project = dossier.project
    reasons: list[str] = []

    if stage == "scope":
        scope = project.scope
        if not scope:
            return ["your project details"]
        if scope.budget_target <= 0.0 or scope.budget_target == -1.0:
            reasons.append("your target budget")
        if scope.budget_ceiling <= 0.0 or scope.budget_ceiling == -1.0:
            reasons.append("your budget ceiling (the most you'd be willing to spend)")
        if not scope.stated_goal or scope.stated_goal.strip().upper() == "TBD":
            reasons.append("the main goal for your remodel")
        pc = scope.property_context
        if not pc or pc.zipcode in ("", "-1"):
            reasons.append("your zip code")
        if not pc or pc.renovation_area <= 0.0:
            reasons.append("the bathroom's approximate size (square footage)")
        if scope.special_considerations is None or scope.special_considerations.allergies is None:
            reasons.append(
                "whether anyone using the bathroom has allergies or sensitivities "
                '(a simple "none" is perfectly fine)'
            )
        if not scope.budget_reality_resolved:
            reasons.append("a quick acknowledgement of the budget reality-check")

    elif stage == "design":
        design = project.design
        if not design or not design.chosen_design:
            reasons.append("which design option you'd like to go with")
        if design and not design.rooms:
            reasons.append("the room measurements")

    elif stage == "safety_permit":
        safety = project.safety_permit
        if safety and any(
            c.tier == "tier_1_professional" and c.depth_consent is None
            for c in safety.classifications
        ):
            reasons.append("your acknowledgement of the professional-only (Tier-1) items")
        if safety and safety.permit_required and not safety.user_permit_consent:
            reasons.append("your consent to obtain the required permit")

    elif stage == "logistics_feasibility":
        logistics = project.logistics_feasibility
        if logistics and logistics.disruption.get("can_live_through_it") is None:
            reasons.append("whether you can live in the home during the remodel")
        if (
            logistics
            and logistics.disruption.get("can_live_through_it") is False
            and not logistics.chosen_displacement
        ):
            reasons.append("where you'll stay while the work is underway")

    elif stage == "materials":
        materials = project.materials
        if materials and any(not item.allergy_screened for item in materials.line_items):
            reasons.append("the allergy screening on your material selections")

    elif stage == "contractor_validation":
        contractor = project.contractor_validation
        if contractor and not contractor.advisory_checklist:
            reasons.append("the contractor advisory checklist")
        if contractor and contractor.quote_provided and not contractor.coverage_check:
            reasons.append("the audit of your contractor quote")
        if diy_eligible_items(dossier) and (contractor is None or contractor.wants_diy is None):
            reasons.append(
                "whether you'll take on the eligible work yourself or use contractors for everything"
            )

    elif stage == "diy_planning":
        diy = project.diy_planning
        if diy and not diy.procedures:
            reasons.append("the DIY procedures for your eligible tasks")
        elif diy:
            eligible = set(diy_eligible_items(dossier))
            decided = {p.item for p in diy.procedures if p.user_feasible is not None}
            if not eligible.issubset(decided):
                reasons.append("a decision on each DIY item (do it yourself, or hand it to a pro)")

    return reasons


app = FastAPI(title="Reno Compass API", version="1.0.0")

# Register correlation ID and telemetry logging middleware
app.add_middleware(TelemetryLoggingMiddleware)

# Mount static folder for frontend assets
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")


class ErrorResponse(BaseModel):
    error_code: str
    message: str
    details: str | None = None
    detail: str | None = None


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    """Custom exception handler for HTTPException to return a structured JSON response."""
    if isinstance(exc.detail, dict):
        error_code = exc.detail.get("error_code", "GENERIC_ERROR")
        message = exc.detail.get("message", "An error occurred.")
        details = exc.detail.get("details")
    else:
        error_code = "GENERIC_ERROR"
        message = str(exc.detail)
        details = None

        # Backward compatibility for plain string HTTPExceptions
        if "Missing session token" in message:
            error_code = "MISSING_SESSION_TOKEN"
            message = "A valid session token is required to execute this operation."
        elif "Missing chat message" in message:
            error_code = "MISSING_CHAT_MESSAGE"
            message = "Chat message content is missing."
        elif "Session expired or not found" in message or "Session not found" in message:
            error_code = "SESSION_NOT_FOUND"
            message = "The requested session could not be found or has expired."
        elif "Dossier is complete" in message:
            error_code = "DOSSIER_COMPLETE"
            message = "The renovation dossier has been finalized, and further chat is closed."
        elif "Failed to parse dossier" in message:
            error_code = "PDF_PARSE_FAILED"
            message = (
                "Could not extract or validate the embedded planning state from the uploaded PDF."
            )
        elif "Stage gate conditions not satisfied" in message:
            error_code = "STAGE_GATE_NOT_SATISFIED"
            message = "Current stage conditions must be fully satisfied before advancing to the next stage."
        elif "LLM agent failed to execute" in message:
            error_code = "LLM_EXECUTION_FAILED"
            parts = message.split("LLM agent failed to execute: ", 1)
            raw_details = parts[1] if len(parts) > 1 else None
            message = "The LLM agent failed to respond. This can occur due to service quotas, regional model availability, or temporary network issues."
            details = raw_details

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error_code": error_code,
            "message": message,
            "details": details,
            "detail": message,
        },
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """Fallback handler for unhandled internal exceptions."""
    logger.exception(f"Unhandled exception encountered: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error_code": "GENERIC_INTERNAL_ERROR",
            "message": "An unexpected error occurred on the server.",
            "details": str(exc),
            "detail": "An unexpected error occurred on the server.",
        },
    )


def _get_dossier_state_summary(dossier: Dossier | None) -> dict:
    """Helper to extract current stage and statuses of all pipeline stages for state-change tracking."""
    if not dossier:
        return {}

    stages_summary = {}
    project = dossier.project
    for stage_key in [
        "scope",
        "design",
        "safety_permit",
        "logistics_feasibility",
        "materials",
        "contractor_validation",
        "diy_planning",
        "synthesis",
    ]:
        stage_obj = getattr(project, stage_key, None)
        if stage_obj and stage_obj.status:
            stages_summary[stage_key] = {
                "state": stage_obj.status.state,
                "user_final_verdict": getattr(stage_obj, "user_final_verdict", None),
            }
        else:
            stages_summary[stage_key] = {"state": "not_started", "user_final_verdict": None}

    return {
        "current_stage": dossier.envelope.current_stage,
        "origin": dossier.envelope.origin,
        "stages": stages_summary,
    }


def _log_dossier_state_change(session_token: str, action: str, before: dict, after: dict):
    """Computes and logs the diff between two dossier states at DEBUG level."""
    if not before:
        logger.debug(
            f"[DOSSIER_STATE_INITIAL] Session: {session_token} | Action: {action} | Initialized State: {json.dumps(after)}"
        )
        return

    changes = []
    if before.get("current_stage") != after.get("current_stage"):
        changes.append(
            f"current_stage: {before.get('current_stage')} -> {after.get('current_stage')}"
        )

    if before.get("origin") != after.get("origin"):
        changes.append(f"origin: {before.get('origin')} -> {after.get('origin')}")

    before_stages = before.get("stages", {})
    after_stages = after.get("stages", {})

    for stage in [
        "scope",
        "design",
        "safety_permit",
        "logistics_feasibility",
        "materials",
        "contractor_validation",
        "diy_planning",
        "synthesis",
    ]:
        b_stage = before_stages.get(stage, {})
        a_stage = after_stages.get(stage, {})

        stage_changes = []
        if b_stage.get("state") != a_stage.get("state"):
            stage_changes.append(f"state: {b_stage.get('state')} -> {a_stage.get('state')}")
        if b_stage.get("user_final_verdict") != a_stage.get("user_final_verdict"):
            stage_changes.append(
                f"user_final_verdict: {b_stage.get('user_final_verdict')} -> {a_stage.get('user_final_verdict')}"
            )

        if stage_changes:
            changes.append(f"stage '{stage}': [{', '.join(stage_changes)}]")

    if changes:
        logger.debug(
            f"[DOSSIER_STATE_CHANGE] Session: {session_token} | Action: {action} | Changes: {'; '.join(changes)}"
        )
    else:
        logger.debug(
            f"[DOSSIER_STATE_CHANGE] Session: {session_token} | Action: {action} | No state changes detected. Current stage: {after.get('current_stage')}"
        )


def _get_agent_for_stage(stage_key: str, dossier: Dossier):
    """Factory resolver mapping stage keys to active Agent classes."""
    agents_map = {
        "scope": ScopeAgent,
        "design": DesignAgent,
        "safety_permit": SafetyAgent,
        "logistics_feasibility": LogisticsAgent,
        "materials": MaterialsAgent,
        "contractor_validation": ContractorAgent,
        "diy_planning": DiyAgent,
        "synthesis": SynthesisAgent,
    }
    agent_class = agents_map.get(stage_key)
    if not agent_class:
        raise ValueError(f"No agent configured for stage: {stage_key}")
    return agent_class(dossier)


def get_client_safe_state(dossier: Dossier) -> dict:
    """Extracts a minimized, safe subset of dossier state for the web client.

    Hides internal dossier data models, budgets, materials, and calculations.
    """
    current_stage = dossier.envelope.current_stage
    conversation = []

    # Extract active stage conversation turns if available
    stage_obj = getattr(dossier.project, current_stage, None)
    if stage_obj and hasattr(stage_obj, "conversation"):
        conversation = [
            {
                "role": turn.role,
                "text": turn.text,
                "at": turn.at.isoformat() if hasattr(turn.at, "isoformat") else str(turn.at),
            }
            for turn in stage_obj.conversation
        ]

    return {"current_stage": current_stage, "conversation": conversation}


@app.get("/")
async def read_index():
    """Serves the main single-page web UI."""
    index_path = "static/index.html"
    if os.path.exists(index_path):
        return FileResponse(index_path)
    return HTMLResponse("<h1>Reno Compass Static UI not found.</h1>")


@app.post("/api/session/new")
async def create_new_session(response: Response):
    """Generates a fresh session token and initialized empty dossier."""
    session_token = f"reno_s_{secrets.token_hex(16)}"
    logger.debug(f"Initializing new session: {session_token}")

    # Construct empty default dossier
    dossier = Dossier(
        envelope=DossierEnvelope(
            dossier_id=session_token,
            schema_version="1.0.0",
            created_at=datetime.utcnow(),
            last_updated_at=datetime.utcnow(),
            origin="fresh",
            current_stage="scope",
        ),
        project=ProjectBody(),
    )

    after_state = _get_dossier_state_summary(dossier)
    _log_dossier_state_change(session_token, "create_new_session", {}, after_state)

    # Save checkpoint
    write_session(session_token, dossier)
    logger.debug(f"Session {session_token} successfully checkpointed.")

    # Set HttpOnly session cookie
    response.set_cookie(
        key="reno_session_token",
        value=session_token,
        httponly=True,
        samesite="strict",
        max_age=settings.session_ttl_seconds,
    )

    safe_state = get_client_safe_state(dossier)
    return {
        "session_token": session_token,
        "current_stage": safe_state["current_stage"],
        "conversation": safe_state["conversation"],
        "quick_replies": _quick_replies_for(dossier),
        "input_hint": _input_hint_for(dossier),
    }


@app.post("/api/session/load")
async def load_session_endpoint(payload: dict):
    """Loads an existing session dossier by token."""
    session_token = payload.get("session_token")
    if not session_token:
        logger.warning("Session load failed: missing session token.")
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "MISSING_SESSION_TOKEN",
                "message": "A valid session token is required to load a session.",
            },
        )

    logger.debug(f"Loading session dossier for token: {session_token}")
    dossier = read_session(session_token)
    if not dossier:
        logger.warning(f"Session expired or not found for token: {session_token}")
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": "SESSION_NOT_FOUND",
                "message": "The requested session could not be found or has expired.",
            },
        )

    safe_state = get_client_safe_state(dossier)
    return {
        "session_token": session_token,
        "current_stage": safe_state["current_stage"],
        "conversation": safe_state["conversation"],
        "quick_replies": _quick_replies_for(dossier),
        "input_hint": _input_hint_for(dossier),
    }


@app.post("/api/chat")
async def chat_endpoint(payload: dict, reno_session_token: str | None = Cookie(None)):
    """Handles chat messages, routing them to the active stage-gate agent."""
    session_token = reno_session_token or payload.get("session_token")
    if not session_token:
        logger.warning("Chat request failed: missing session token.")
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "MISSING_SESSION_TOKEN",
                "message": "A valid session token is required to execute this operation.",
            },
        )

    message = payload.get("message")
    if not message:
        logger.warning(f"Chat request failed for session {session_token}: missing chat message.")
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "MISSING_CHAT_MESSAGE",
                "message": "Chat message content is missing.",
            },
        )

    # Load session
    logger.debug(f"Loading session dossier for token: {session_token}")

    dossier = read_session(session_token)
    logger.debug(f"Loaded dossier: {json.dumps(dossier, default=str)} for token: {session_token}")
    if not dossier:
        logger.warning(f"Session expired or not found for token: {session_token}")
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": "SESSION_NOT_FOUND",
                "message": "The requested session could not be found or has expired.",
            },
        )

    before_state = _get_dossier_state_summary(dossier)

    current_stage = dossier.envelope.current_stage
    logger.debug(f"Session {session_token} is currently in stage: {current_stage}")
    if current_stage == "complete":
        logger.warning(f"Chat request rejected: Session {session_token} dossier is complete.")
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "DOSSIER_COMPLETE",
                "message": "The renovation dossier has been finalized, and further chat is closed.",
            },
        )

    # Resolve agent
    agent = _get_agent_for_stage(current_stage, dossier)

    stage_obj = getattr(dossier.project, current_stage, None)
    if not stage_obj:
        stage_obj = agent._create_default_stage_object(current_stage)
        setattr(dossier.project, current_stage, stage_obj)

    from domain.dossier import ConversationTurn

    # Append user turn to conversation history
    if stage_obj and hasattr(stage_obj, "conversation"):
        stage_obj.conversation.append(
            ConversationTurn(role="user", text=message, at=datetime.utcnow())
        )

    # Record any DIY/Contractor decision BEFORE the agent runs, so the DIY seeding
    # pass advances to the next item and the agent presents it (rather than repeating
    # the item just decided). Contractor's all-or-none choice doubles as a proceed
    # signal; a per-item "decided" moves the loop forward but does NOT end the stage.
    contractor_diy_choice = _apply_contractor_diy_choice(dossier, message)
    diy_item_decision = _apply_diy_item_decision(dossier, message)

    # Run model chat
    try:
        logger.debug(f"Running agent {agent.__class__.__name__} for chat processing.")
        agent_response = agent.run_chat(message)
        logger.debug("Agent response successfully generated.")

        # Append agent response to conversation history
        if stage_obj and hasattr(stage_obj, "conversation"):
            stage_obj.conversation.append(
                ConversationTurn(role="agent", text=agent_response, at=datetime.utcnow())
            )

        # Run structured parameter extraction pass to update dossier fields
        logger.debug("Executing post-chat structured parameter extraction pass.")
        agent.extract_and_update_stage_dossier()

        # Advancement is driven by the USER's own confirmation — NEVER by the agent's
        # opinion. The [APPROVE_STAGE_TRANSITION] tag is the model's readiness signal,
        # not the family's consent, so it is stripped from the reply but does NOT advance
        # the pipeline on its own. A real advance needs one of:
        #   * a deterministic proceed-intent in the USER's message ("proceed", "move on",
        #     "finalize", …), OR
        #   * a short affirmation ("yes", "ok", "sounds good") — but ONLY at the decision
        #     boundary, so a stray "yes" mid-Q&A never advances, OR
        #   * the Contractor all-or-none DIY choice (which itself routes the pipeline).
        # The gate check additionally covers RESUME (a stage confirmed in a prior session
        # whose verdict already persists).
        tag_present = bool(_TRANSITION_TAG_RE.search(agent_response))  # advisory only
        # Strip the control tag (bracketed or bare) from anything shown to the customer.
        agent_response = _TRANSITION_TAG_RE.sub("", agent_response).strip()
        if stage_obj and hasattr(stage_obj, "conversation") and stage_obj.conversation:
            stage_obj.conversation[-1].text = agent_response

        ready = _stage_ready_to_confirm(dossier, current_stage)
        proceed_intent = _is_proceed_intent(message)
        affirm_at_boundary = ready and _is_affirmation(message)
        user_confirmed = proceed_intent or affirm_at_boundary or contractor_diy_choice
        if tag_present:
            logger.info("Stage-ready tag seen (advisory; does not advance on its own).")
        if proceed_intent:
            logger.info("Advance trigger: explicit user proceed-intent detected.")
        if affirm_at_boundary:
            logger.info("Advance trigger: user affirmation at the decision boundary.")
        if contractor_diy_choice:
            logger.info("Advance trigger: contractor-stage all-or-none DIY choice recorded.")
        if diy_item_decision:
            logger.info(f"DIY per-item decision recorded: {diy_item_decision}.")
        # Record the user's verdict ONLY when they confirm AND the stage is genuinely
        # ready. This prevents a "sticky" verdict from a premature confirm that would
        # later auto-advance the moment the last data field fills in.
        confirmed_and_ready = user_confirmed and ready
        if confirmed_and_ready and hasattr(stage_obj, "user_final_verdict"):
            stage_obj.user_final_verdict = True

        advanced = False
        if confirmed_and_ready or evaluate_stage_gate(dossier, current_stage):
            ok = advance_pipeline(dossier)
            if ok:
                advanced = True
                next_stage = dossier.envelope.current_stage
                logger.info(f"Pipeline advanced automatically to next stage: {next_stage}")

                if next_stage != "complete":
                    # Seed next stage conversation greeting
                    next_agent = _get_agent_for_stage(next_stage, dossier)
                    next_stage_obj = getattr(dossier.project, next_stage, None)
                    if not next_stage_obj:
                        next_stage_obj = next_agent._create_default_stage_object(next_stage)
                        setattr(dossier.project, next_stage, next_stage_obj)

                    next_welcome_user_msg = (
                        f"Let's get started on the {next_stage.replace('_', ' ')} stage."
                    )
                    # SynthesisStage is a terminal mirror with no conversation log —
                    # generate its summary but don't append to a non-existent field.
                    has_convo = hasattr(next_stage_obj, "conversation")
                    if has_convo:
                        next_stage_obj.conversation.append(
                            ConversationTurn(
                                role="user", text=next_welcome_user_msg, at=datetime.utcnow()
                            )
                        )
                    next_welcome_response = next_agent.run_chat(next_welcome_user_msg)
                    if has_convo:
                        next_stage_obj.conversation.append(
                            ConversationTurn(
                                role="agent", text=next_welcome_response, at=datetime.utcnow()
                            )
                        )

                    # DIY presents its FIRST eligible item in this entry greeting, while
                    # that item is the active one. Extract now so its authored steps/tools
                    # are captured against item #1 — the next turn records the family's
                    # decision and advances the loop to item #2, so this is the only moment
                    # item #1 is both authored and active.
                    if next_stage == "diy_planning":
                        next_agent.extract_and_update_stage_dossier()

                    # Combine responses for user presentation
                    agent_response = f"{agent_response}\n\n{next_welcome_response}"
                else:
                    agent_response = (
                        f"{agent_response}\n\n"
                        "Congratulations! Your bathroom renovation plan is complete. "
                        "You can download the blueprints using the button at the top right."
                    )
        if user_confirmed and not advanced:
            # The user asked to move on but the pipeline did NOT advance — a gate
            # condition is still unmet (e.g. an unanswered Tier-1 acknowledgement or
            # permit consent). Name EXACTLY what's missing so they can resolve it instead
            # of re-confirming into a loop. This MUST live OUTSIDE the advance-attempt
            # block above: when the gate cannot pass, that block is skipped entirely, so a
            # warning nested inside it would never fire (the silent-loop bug).
            logger.warning(
                f"Auto-advance block: stage gate requirements not met for {current_stage}"
            )
            reasons = _gate_missing_reasons(dossier, current_stage)
            if reasons:
                # Name EXACTLY what's missing so the user gives the real blocker, instead
                # of re-confirming into a loop. Never invite "yes, proceed" here — the gate
                # cannot open until these are answered.
                if len(reasons) == 1:
                    needed = reasons[0]
                else:
                    needed = "; ".join(reasons[:-1]) + f"; and {reasons[-1]}"
                agent_response = (
                    f"{agent_response}\n\n"
                    f"We're almost there — before we move on, I still need {needed}. "
                    "Share that and we'll continue."
                )
            else:
                # Data is complete; only the confirmation itself was needed (rare — the
                # verdict was just set, so a retry will advance).
                hint = _STAGE_BLOCK_HINTS.get(current_stage, "the details for this stage")
                agent_response = (
                    f"{agent_response}\n\n"
                    f"Before we move on, I'm making sure {hint} is fully captured on my end. "
                    "If you've already covered this, just reply \"yes, proceed\" and I'll lock it in; "
                    "otherwise let me know what to adjust."
                )
    except Exception as exc:
        logger.exception(f"LLM agent execution failed for session {session_token}: {exc}")
        raise HTTPException(
            status_code=500,
            detail={
                "error_code": "LLM_EXECUTION_FAILED",
                "message": "The LLM agent failed to respond. This can occur due to service quotas, regional model availability, or temporary network issues.",
                "details": str(exc),
            },
        )

    after_state = _get_dossier_state_summary(dossier)
    _log_dossier_state_change(session_token, "chat_endpoint", before_state, after_state)

    # Checkpoint session state
    write_session(session_token, dossier)
    logger.debug(f"Session checkpointed for token: {session_token}")

    # Final safety net: the control tag must NEVER reach the customer, on any path
    # (including a seeded next-stage greeting appended above).
    agent_response = _TRANSITION_TAG_RE.sub("", agent_response).strip()

    safe_state = get_client_safe_state(dossier)
    return {
        "response": agent_response,
        "current_stage": safe_state["current_stage"],
        "conversation": safe_state["conversation"],
        "quick_replies": _quick_replies_for(dossier),
        "input_hint": _input_hint_for(dossier),
    }


@app.post("/api/session/advance")
async def advance_stage_endpoint(payload: dict):
    """Attempts to advance the pipeline to the next stage gate."""
    session_token = payload.get("session_token")
    if not session_token:
        logger.warning("Stage advance failed: missing session token.")
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "MISSING_SESSION_TOKEN",
                "message": "A valid session token is required to execute this operation.",
            },
        )

    logger.debug(f"Loading session {session_token} for stage advancement.")
    dossier = read_session(session_token)
    if not dossier:
        logger.warning(f"Stage advance failed: session {session_token} not found.")
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": "SESSION_NOT_FOUND",
                "message": "The requested session could not be found or has expired.",
            },
        )

    before_state = _get_dossier_state_summary(dossier)

    current_stage = dossier.envelope.current_stage
    logger.debug(f"Advancing stage for session {session_token} (current: {current_stage})")

    # Mark user verdict as true (user approved transition)
    project = dossier.project
    stage_obj = getattr(project, current_stage, None)
    if stage_obj and hasattr(stage_obj, "user_final_verdict"):
        logger.debug(f"Setting user_final_verdict = True for stage {current_stage}")
        stage_obj.user_final_verdict = True

    ok = advance_pipeline(dossier)
    if not ok:
        logger.warning(
            f"Stage gate conditions not satisfied for {current_stage}. Blocked advancement."
        )
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "STAGE_GATE_NOT_SATISFIED",
                "message": "Current stage conditions must be fully satisfied before advancing to the next stage.",
            },
        )

    after_state = _get_dossier_state_summary(dossier)
    _log_dossier_state_change(session_token, "advance_stage_endpoint", before_state, after_state)

    write_session(session_token, dossier)
    logger.info(
        f"Session {session_token} successfully advanced from {current_stage} to {dossier.envelope.current_stage}"
    )
    safe_state = get_client_safe_state(dossier)
    return {
        "current_stage": safe_state["current_stage"],
        "conversation": safe_state["conversation"],
        "quick_replies": _quick_replies_for(dossier),
        "input_hint": _input_hint_for(dossier),
    }


@app.post("/api/session/restore-pdf")
async def restore_from_pdf(file: UploadFile = File(...), response: Response = None):
    """Restores session state by parsing embedded JSON from an uploaded blueprint PDF."""
    logger.debug("Received request to restore session from PDF upload.")
    try:
        pdf_bytes = await file.read()
        dossier_json = extract_dossier_json_from_pdf(pdf_bytes)

        # Validate schema version compatibility (SemVer / Dimension 11)
        data = json.loads(dossier_json)
        dossier = Dossier.model_validate(data)
        logger.debug(
            f"Parsed dossier JSON successfully from PDF. ID: {dossier.envelope.dossier_id}"
        )
    except Exception as exc:
        logger.exception(f"Failed to parse dossier from PDF: {exc}")
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "PDF_PARSE_FAILED",
                "message": "Could not extract or validate the embedded planning state from the uploaded PDF.",
                "details": str(exc),
            },
        )

    imported_state = _get_dossier_state_summary(dossier)

    # Enforce untrusted portable import rules (SI-4)
    # Untrusted import resets to Scope for re-walk verification
    dossier.envelope.origin = "session_restore"

    # Save as new session
    session_token = f"reno_s_{secrets.token_hex(16)}"
    dossier.envelope.dossier_id = session_token
    dossier.envelope.current_stage = "scope"

    logger.debug(
        f"Enforcing untrusted portable import rules: resetting stage to 'scope' for verification. New session token: {session_token}"
    )
    # Reset downstream nodes to enforce re-walk validation
    reopen_stage_and_cascade(dossier, "scope")

    final_state = _get_dossier_state_summary(dossier)
    _log_dossier_state_change(session_token, "restore_from_pdf_imported", {}, imported_state)
    _log_dossier_state_change(session_token, "restore_from_pdf_final", imported_state, final_state)

    write_session(session_token, dossier)
    logger.debug(f"Restored session checkpointed: {session_token}")

    if response:
        response.set_cookie(
            key="reno_session_token",
            value=session_token,
            httponly=True,
            samesite="strict",
            max_age=settings.session_ttl_seconds,
        )

    safe_state = get_client_safe_state(dossier)
    return {
        "session_token": session_token,
        "current_stage": safe_state["current_stage"],
        "conversation": safe_state["conversation"],
        "warning": "Untrusted import. Session reset to Scope for re-walk validation.",
    }


@app.post("/api/session/download-artifacts")
async def download_artifacts(payload: dict):
    """Generates and returns base64 string payloads of final PDF and XLSX documents."""
    session_token = payload.get("session_token")
    if not session_token:
        logger.warning("Download artifacts failed: missing session token.")
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "MISSING_SESSION_TOKEN",
                "message": "A valid session token is required to execute this operation.",
            },
        )

    logger.debug(f"Loading session {session_token} for artifact generation.")
    dossier = read_session(session_token)
    if not dossier:
        logger.warning(f"Download artifacts failed: session {session_token} not found.")
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": "SESSION_NOT_FOUND",
                "message": "The requested session could not be found or has expired.",
            },
        )

    # Render files
    logger.debug(f"Generating PDF and XLSX blueprints for session: {session_token}")
    pdf_base64 = generate_dossier_pdf(dossier)
    xlsx_base64 = generate_materials_xlsx(dossier)
    logger.info(f"Artifacts successfully compiled for session {session_token}.")

    return {
        "pdf_base64": pdf_base64,
        "xlsx_base64": xlsx_base64,
        "pdf_filename": "reno_compass_blueprint.pdf",
        "xlsx_filename": "reno_compass_materials.xlsx",
    }


@app.post("/api/session/finalize")
async def finalize_session_endpoint(payload: dict):
    """Removes a COMPLETED session's checkpoint from storage.

    Called by the client once the plan is complete and the artifacts have been
    downloaded (the client keeps a copy for "Download Again"). We only delete a
    session that has actually reached the terminal ``complete`` stage — this guards
    against wiping an in-progress session — and deletion is best-effort so a storage
    hiccup never surfaces as a user-facing error. "Restore from PDF" is unaffected:
    it rebuilds state from the uploaded blueprint, not from this checkpoint.
    """
    session_token = payload.get("session_token")
    if not session_token:
        logger.warning("Finalize failed: missing session token.")
        raise HTTPException(
            status_code=400,
            detail={
                "error_code": "MISSING_SESSION_TOKEN",
                "message": "A valid session token is required to execute this operation.",
            },
        )

    dossier = read_session(session_token)
    # Already gone (e.g. a second finalize call) — treat as success, nothing to do.
    if dossier is None:
        return {"deleted": False, "reason": "not_found"}
    if dossier.envelope.current_stage != "complete":
        logger.info(
            f"Finalize skipped for {session_token}: stage is "
            f"{dossier.envelope.current_stage!r}, not 'complete'."
        )
        return {"deleted": False, "reason": "not_complete"}

    deleted = delete_session(session_token)
    logger.info(f"Finalize for {session_token}: checkpoint deleted={deleted}.")
    return {"deleted": deleted}
