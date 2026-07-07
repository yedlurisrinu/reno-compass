---
name: cross-cutting-concerns
description: Always-active implementation concerns spanning all stages — logging, safety audit trail, error handling, tool-failure policy.
---

# Rule — Cross-Cutting Concerns (always active)

Implementation concerns that span every stage. Full spec: `reno-compass-cross-cutting.md` (CC-1..8). The
architecture-shaping ones (P1) are summarized here because they govern behavior in every stage.

## Logging + safety audit trail (CC-1)
- Structured (JSON) logs; correlation id = session token; log every stage transition, gate decision, tool call.
- SAFETY-DECISION AUDIT TRAIL: append-only, immutable record of every tier classification (item, tier, source,
  envelope), every Tier-1 consent, every permit disclosure. Persisted separately from the dossier and OUTLIVES
  it. Records ONLY safety data — MUST NOT contain sensitive personal fields (allergies/health/accessibility);
  carrying no sensitive data is what lets it outlive the dossier's TTL purge (DM-2 store #5 / DM-11). Never
  mutated.
- REDACTION AT THE LOG BOUNDARY (mandatory): redact/hash SENSITIVE fields (allergies, health, accessibility)
  and NEVER log raw contractor-quote text (log a hash + findings). Applies everywhere a log/trace is emitted.

## Error taxonomy (CC-2) — one taxonomy, every stage
- USER-RECOVERABLE (bad input, unit mismatch): surface, ask correction, do NOT open the gate.
- RETRYABLE (transient tool/LLM/network): bounded retry (CC-3), then degrade or surface.
- DEGRADED-MODE (capability down, pipeline continues honestly): explicit fallback, told to the user
  (e.g. unreadable quote → advisory-only; search miss → proceed without the item).
- HARD-FAIL (invariant violated): stop; never fabricate forward.
Principle: never improvise past missing/failed information — surface or degrade, never silently guess.

## Tool-failure & retry (CC-3)
- Compute tools (cost/geometry/quantity): retry → HARD-FAIL the stage (a wrong number is worse than a stop).
- Generation tools (PDF/xlsx): retry → surface (regenerable).
- Web search (missing item): retry → DEGRADE (proceed without; flag for the deferred suggested-items store).
  A search failure returns "not found", NEVER a guessed value (SI-29 boundary applied to search).
- Safety validations (envelope check, allergy screen) that fail to RUN block the gate — can't confirm safe =
  not confirmed; never pass by default.

## Deployment concerns (CC-5/6/7, summary)
Rate-limit identity-less sessions (per-token + global ceiling); checkpoint writes ATOMIC (write-new-then-swap)
+ idempotent; externalize config/secrets incl. the frozen-reference-data VERSION POINTER (a stale pointer prices
against old bands). Full detail: CC-5/6/7 in the source artifact.
