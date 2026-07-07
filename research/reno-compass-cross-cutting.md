# Reno Compass — Cross-Cutting Concerns (CC)

Implementation concerns that span EVERY stage and belong to none — the aspects a stage-organized spec
under-specifies precisely because they live across stages. These are instructions to the implementation
(Antigravity codegen), not agent behavior. Numbered CC-n, stable. Priority tag: [P1] must-specify (shapes
architecture; costly to retrofit), [P2] deployment-shaped, [P3] name-and-defer.

Already specified elsewhere (not repeated here): persistence/checkpoint (DM), session/TTL (DM-5), structured-
output validation boundary (SI-29), prompt-injection defense (SI-24), safety re-derivation on load (SI-4).

---

## CC-1. Logging, observability & the SAFETY-DECISION AUDIT TRAIL [P1]
*Coverage: audit-trail + redaction = SCENARIO (TS-50, TS-51); JSON format + correlation id = code-review.*
Two distinct needs — keep them separate:
- **Operational logging:** structured (JSON) logs; correlation id = the session token; standard levels
  (DEBUG/INFO/WARN/ERROR). Log every stage transition, gate open/close (+ which guard passed/failed), tool
  invocation + result-or-failure, and verdict emitted.
- **Safety-decision audit trail (first-class, NOT generic logging):** an append-only, immutable record of every
  tier classification (item, tier, source rule, envelope), every Tier-1 consent (what was consented, when), and
  every permit disclosure. Rationale: a tool that classifies structural/electrical/gas work needs a defensible
  record of what it told the family and what they consented to — liability-adjacent, not a nicety. This trail
  is derived from the dossier's `[safety]` fields but persisted separately so it survives even if a dossier is
  discarded. Never mutated, only appended. RETENTION (reconciled with DM-2 store #5 / DM-11): records ONLY
  safety classifications, consents, sources, and envelopes — MUST NOT contain sensitive personal fields
  (allergies/health/accessibility). Carrying no sensitive data is exactly what lets it outlive the dossier's
  TTL purge without violating DM-11.
- **REDACTION AT THE LOG BOUNDARY (mandatory):** logs and traces will otherwise capture SENSITIVE fields
  (allergies, health, accessibility — SI-6) and the UNTRUSTED quote text (SI-24). Redact/hash sensitive fields
  before they reach any log sink; never log raw quote text (log a content hash + audit findings, not the body).

## CC-2. Error handling & failure taxonomy [P1]
*Coverage: degraded-mode + never-improvise = SCENARIO (TS-6, TS-52); taxonomy structure = code-review.*
A single taxonomy every stage uses, so Antigravity does not invent one per stage. Four classes:
- **USER-RECOVERABLE** (bad/implausible input, unit mismatch, missing required field): surface plainly, ask for
  correction, do NOT advance the gate. Ex: allowance unit-mismatch (SI-16), implausible measurement (SI-3).
- **RETRYABLE** (transient tool/network/LLM failure): bounded retry (see CC-3), then degrade or surface.
- **DEGRADED-MODE** (a capability is unavailable but the pipeline can continue honestly): explicit fallback,
  told to the user. Ex: unreadable quote → advisory-only mode (SI-24); web-search miss → proceed without the
  suggested item.
- **HARD-FAIL** (invariant violated — schema-major mismatch, unresolvable safety state): stop, do not fabricate
  forward. Ex: schema major-version mismatch (DM-8), broken safety ref that cannot re-derive.
Principle: NEVER improvise past missing/failed information (mirrors the gate discipline). A failure is surfaced
or degraded, never silently guessed around.

## CC-3. Tool-failure & retry policy [P1]
*Coverage: safety-validation-fails-blocks-gate + search-never-guesses = SCENARIO (TS-52; SI-29 boundary); retry/backoff counts = code-review.*
Deterministic tools (cost lookup, quantity/waste, geometry, PDF/xlsx generation, envelope check, allergy screen,
web search) each declare: timeout, retry count (bounded, exponential backoff), and on-exhaustion behavior.
- Compute tools (cost/geometry/quantity): retry then HARD-FAIL the stage (a wrong number is worse than a stop).
- Generation tools (PDF/xlsx): retry then surface (deliverable can be regenerated).
- Web search (missing-item lookup): retry then DEGRADE (proceed without; item flagged for the deferred
  suggested-items store). NEVER let a search failure hallucinate a value — the tool returns "not found," not a
  guess (this is the SI-29 boundary applied to search).
- Safety-critical validations (envelope check, allergy screen) that fail to RUN block the gate (can't confirm
  safe → not confirmed), rather than passing by default.

## CC-4. LLM observability & cost [P3]
*Coverage: code-review only (not agent-observable).*
Per stage/turn: token counts, latency, model identity, retry occurrences. A multi-stage pipeline compounds cost;
surface per-session token/cost so runaway loops are visible. Ties to CC-1 correlation id.

## CC-5. Rate limiting & abuse [P2]
*Coverage: code-review only (not agent-observable).*
Identity-less sessions (no login, DM-5) give no natural throttle, and an anonymous endpoint fronting an LLM is a
cost-exposure surface. Specify at minimum: per-session-token rate limit + a global ceiling; reject-with-retry-
after past the limit. Distinguish a legitimate multi-evening user (sliding-72h TTL is fine) from a hot loop.

## CC-6. Checkpoint atomicity & idempotency [P2]
*Coverage: code-review only (not agent-observable).*
Single-writer per session (DM-5) removes multi-writer races, but still specify: checkpoint writes are ATOMIC
(write-new-then-swap, never partial overwrite of the live object) so a crash mid-checkpoint can't corrupt the
dossier; and idempotent (re-applying the same checkpoint is a no-op). On read, validate before trust (DM-9).

## CC-7. Configuration & secrets [P2]
*Coverage: code-review only (not agent-observable).*
Externalize: GCS bucket/credentials, model endpoint(s), the FROZEN-REFERENCE-DATA VERSION POINTER (which RD
snapshot is live — ties to DM-8/DM-10 recompute-on-version-change), TTL constants, rate-limit constants. No
hardcoded secrets; config is environment-driven. The reference-data version is the one config with correctness
impact — a stale pointer silently prices against old bands.

## CC-8. Time & localization [P3]
*Coverage: code-review only (not agent-observable).*
TTL expiry and timestamps are timezone-explicit (store UTC, present local). Locale assumptions are surfaced, not
hidden: the frozen reference data is US/region-scoped (regional cost factor, IRC/NEC, Title-24) — the same
extend-in-lockstep rule as domain scoping (AM-12) applies to jurisdiction. Timelines remain industry-average +
best-case (a product convention, already in-spec).

---

## Priority summary (for the Antigravity hand-off)
- **[P1] specify before implementation (shapes code structure):** CC-1 logging+audit-trail, CC-2 error
  taxonomy, CC-3 tool-failure/retry. Retrofitting these means rework.
- **[P2] deployment-shaped:** CC-5 rate limiting, CC-6 checkpoint atomicity, CC-7 config/secrets.
- **[P3] name-and-defer:** CC-4 LLM observability, CC-8 time/localization.
The single hardest flag for this domain: CC-1's safety-decision audit trail — first-class, immutable,
liability-adjacent, not folded into generic logging.
