# Reno Compass — Data Model & Persistence (DM)

The persistence-layer contract. The dossier schema defines the *shape* of state; this defines how it is
STORED, KEYED, EXPIRED, RECOVERED, and TRUSTED. Numbered DM-n, stable. Settled decisions marked ✓; open items
marked ◻ for follow-up.

Grounding constraints (already decided elsewhere, not re-litigated here): dossier = sole source of truth
(SI-5); safety fields ALWAYS re-derive on restore, never trusted from file (SI-4); save/restore = resume-
in-progress; `complete` is terminal (SI-34); Antigravity managed agent has no structured-output enforcement,
so schema conformance is code-validated at the tool boundary (SI-29), NOT provider-guaranteed.

---

## DM-1. Deployment shape ✓
Chat frontend (or API client) → FastAPI application fronting the agent. Persistence lives in the FastAPI layer,
not in the `.agents` runtime. The structured-output constraint is a TOOL-BOUNDARY concern (validate-on-write),
independent of and upstream of persistence.

## DM-2. The four stores (distinct trust + lifetime) ✓
1. **Dossier (session state)** — one user's in-progress renovation. Server-side checkpoint, single-writer,
   crash-recoverable. TRUSTED (server-owned).
2. **Vetted reference data (RD-1..5)** — frozen, curated, human-validated. Read-only, shared, high-trust.
   Lives in the `.agents` skills; not written at runtime.
3. **Suggested-items store** — generalized SI-23: any web-search result NOT in the vetted set is persisted
   append-only as a candidate for human review before merge into the vetted RDs. Shared, UNTRUSTED-until-vetted.
4. **Accounts / identity** — DEFERRED (roadmap). Its absence is what makes session recovery token-based (DM-5).
5. **Safety-decision audit trail (CC-1)** — append-only, immutable record of every tier classification (item,
   tier, source rule, envelope), Tier-1 consent, and permit disclosure. Persisted SEPARATELY from the dossier
   and OUTLIVES it (survives dossier discard/TTL purge) — this is deliberate: it is the liability-adjacent
   record of what the tool classified and what the family consented to. RETENTION RECONCILIATION (with DM-11):
   the trail records ONLY safety classifications/consents/sources/envelopes — NOT sensitive personal data
   (allergies/health/accessibility). Because it carries no sensitive fields, it can outlive the dossier without
   violating the DM-11 purge. The implementation MUST NOT write sensitive fields into this store.

## DM-3. Dossier persistence — medium, format, cadence ✓
- ✓ MEDIUM: Google Cloud Storage (GCS) bucket — the S3-equivalent object store. Access pattern is pure
  key→whole-document (resume loads the entire dossier; never a partial query), so an object store fits and a
  database is unneeded for the demo. Object key = the session token (DM-5); one object per session,
  overwritten each checkpoint. The same object doubles as the portable export (DM-6) — same bytes, downloadable.
- ✓ CADENCE: checkpoint every ~2 minutes AND on every stage-gate transition. A crash loses at most ~2 min /
  the current in-progress stage's unsaved turns.
- ✓ EXPIRY: 30-day absolute via a GCS lifecycle rule (object auto-deleted); the sliding-72h is a `last_active`
  timestamp the FastAPI layer checks (DM-5). Firestore is the upgrade IF/when accounts land and per-user
  session queries are needed — deferred alongside accounts.
- ✓ FORMAT: JSON (API/tooling ubiquity; validated on write at the tool boundary per SI-29, since the provider
  does not guarantee structured output).

## DM-4. Durability tiers — what persists vs re-derives ✓
Every dossier field falls in ONE tier:
- **Persisted-and-trusted:** scope, design options + `chosen_design`, verdicts, `active_option_role`,
  `retained_analysis`, SectionStatus, `current_stage`, timestamps, gap_amount. Restored as-is.
- **Persisted-but-re-derived (safety carve-out, SI-4):** all `[safety]` fields — classifications, consent,
  envelopes. Persisted for continuity/audit BUT re-derived on restore; the file copy is never trusted for a
  gate decision. This is also the tamper defense on the untrusted import path (DM-6).
- **Archived-not-working-memory (SI-33):** raw conversation turns for completed stages — archived, reversible,
  not in active context; the carried-forward summary is a prompt aid, not a state store.
- **Never-persisted:** transient per-turn scratch.
- ✓ Explicit field→tier table (against the current schema):

| Dossier section / field | Tier | Note |
|---|---|---|
| `dossier_id`, `schema_version`, `current_stage`, `session_id`, timestamps | Persisted-trusted | orchestration + identity |
| `scope.*` (goal, property_context, priorities, budget, timing) | Persisted-trusted | user-provided facts |
| `scope.special_considerations.*` (SENSITIVE) | Persisted-trusted | at-rest per DM-11; 3-state preserved |
| `design.options[]`, `chosen_design`, `active_option_role`, `retained_analysis` | Persisted-trusted | design + retention are trusted |
| `design.*.refined_estimate` and other `[computed]` (quantities, totals, cost lookups) | Persisted-trusted **value** + recompute-on-version-mismatch | DM-10 |
| `safety_permit.*` — classifications, consent, envelopes `[safety]` | **Persisted-but-re-derived** | SI-4; persisted for continuity/audit, never trusted for a gate |
| `logistics_feasibility.*` (verdict, total_with_displacement, feasibility bools) | Persisted-trusted | verdict is a user/computed decision |
| `materials.*` (line_items, allowances, final_total) | Persisted-trusted | but `envelope_check`/`allergy_screened` re-run on load (code validations) |
| `contractor_validation.*` (audit, flags, advisory) | Persisted-trusted | quote_raw_text retained as audited data |
| `diy_planning.*` (procedures, tools) | Persisted-trusted | `applicable` is DERIVED, not stored |
| `synthesis.*` (pdf_ref, phase_checklists, budget_gap_bridge, design_accepted, has_budget_gap) | Persisted-trusted | terminal outputs |
| SectionStatus, confirmation_revoked (all sections) | Persisted-trusted | resume the state machine |
| Raw conversation turns (completed stages) | Archived (SI-33) | reversible; summary carried forward, not a state store |
| Per-turn scratch / transient reasoning | Never-persisted | |

Rule of thumb: everything is persisted-trusted EXCEPT (a) `[safety]` fields — persisted but re-derived on load
(SI-4), (b) the material code-validations (`envelope_check`, `allergy_screened`) which re-run on load, (c) raw
turns which are archived not working-memory, (d) transient scratch which is never persisted. `[computed]` values
are persisted for fast restore but recomputed on a version mismatch (DM-10).

## DM-5. Session identity, lifetime, TTL ✓
- Identity-less: the ONLY link between user and their server-side dossier is an opaque session token the client
  holds (browser cookie / localStorage for the chat app; returned-and-resent id for API clients).
- **Sliding TTL 72h** (refreshed each interaction) + **absolute cap 30d** regardless of activity. Generous
  because renovation planning spans multiple evenings; self-cleaning so anonymous dossiers don't accumulate
  unbounded (no identity to attribute orphans to).
- Single-writer by nature (one token = one session) → no concurrency/locking needed. (Reopens IF accounts land.)

## DM-6. Recovery model + portable export (first-class) ✓
Recoverable via server checkpoint: browser/tab close & reopen (cookie replays token) · app/API restart (token
resent) · crash (to last checkpoint, losing only since-checkpoint). NOT recoverable server-side: cleared
browser data · different device · lost token — these are the irreducible limit of no-identity.
- **Portable export is the DESIGNATED, PROMOTED recovery path** for what tokens can't cover (Option A): the app
  surfaces a save nudge at risky moments (before long gaps, on explicit exit), positions export as "pick up
  anywhere," and documents it as the recovery answer.
- Import is UNTRUSTED → SI-4 re-derivation of safety fields is the tamper defense (a tampered dossier cannot
  inject a false safety classification; Safety recomputes). No extra checksum required for the demo; accounts
  are the eventual upgrade that removes the lost-token cliff entirely.

## DM-7. Identity & keys ✓
- ✓ `session_id` (token, DM-5); `dossier_id` (generate-on-fresh, preserve-on-restore, existing schema field).
- ✓ EXPLICIT STABLE IDs (not positional) for classifications, line_items, rooms, and options — survives list
  reordering/removal on a revisit so cross-references (envelope re-open T10/T4a, room_ref rollups) resolve
  correctly after a reload. Positional indices were rejected: a mis-resolved envelope ref after reload could
  pair a product with the wrong tier (safety-adjacent correctness). `option_role` already keys the retention
  map. IDs are opaque, stable for the item's lifetime, regenerated only when the item is genuinely new.

## DM-8. Schema versioning & migration ✓
- ✓ `schema_version` exists; restore does a compatibility check.
- ✓ SEMVER. On load, compare dossier `schema_version` to current: MAJOR mismatch → REJECT with a clear message
  ("this plan was made with an older version; please start fresh") — no migration machinery for the demo, which
  is honest and safe. MINOR/patch mismatch → best-effort load (additive changes tolerated). Matters most on the
  portable-export path (server checkpoints are short-lived within the 30d cap).

## DM-9. Referential integrity on load ✓
Cross-references must resolve after restore: classification→envelope, line_item→room_ref,
retained_analysis→option_role, chosen_design→option. ✓ POLICY: a load-time validation pass checks them. A broken
SAFETY ref self-heals (safety re-derives anyway, DM-4). A broken DESIGN/MATERIALS ref → fall to the UNTRUSTED
re-walk path (treat the load like a portable import): the re-walk + RC regenerates the references cleanly. This
reuses existing machinery (DM-13 untrusted path) instead of inventing repair logic. No silent in-place repair.

## DM-10. Computed-field policy ✓
✓ Persist computed VALUES (fast restore) AND recompute when the schema/reference version differs from the saved
one — sharing DM-8's version check (one mechanism, not two). Normal restore is instant; a dossier saved before a
reference-table change self-corrects on load. Inputs remain in the dossier (design/materials), so recompute is
always possible.

## DM-11. Sensitive data at rest ✓
- ✓ 3-state (`value`/`skipped`/`null`) and the allergy confirmed-empty `[]` semantics are preserved exactly on
  serialize/restore (SI-6 integrity).
- ✓ Server checkpoint holds sensitive fields; they are PURGED automatically when the dossier hits its TTL (no
  separate lifecycle — the GCS lifecycle rule that deletes the dossier removes them). ✓ Portable export is
  COMPLETE (no redaction for the demo) — a redacted export couldn't fully restore (allergy screen would re-flag
  as unscreened). The user is TOLD the export contains their personal details, since it is user-held by their
  choice. Redaction is an accounts-era feature, deferred with accounts.

## DM-12. Suggested-items store — shape ◻
Generalized SI-23 feedback loop. ◻ Define: record shape (rd_category, item, source_url, first_seen, session_ref,
review_status), append-only write on a web-search miss, and the human-review→merge-into-vetted workflow. This is
the one runtime-WRITTEN shared store; keep it strictly separated from the frozen vetted RDs (no auto-promotion —
mirrors the no-auto-poisoning rule).

---

## DM-13. Two restore paths — trust differs, safety re-derivation does NOT ✓
The session token is the single connecting piece for BOTH browser (cookie) and API (returned/resent id) clients
(one identity mechanism, DM-5). But there are two RESTORE sources with different trust, and they behave
differently — EXCEPT for safety, which is invariant across both.

- **GCS server checkpoint (TRUSTED, server-owned):** resume SEAMLESSLY — pick up exactly where the user left
  off, NO re-walk, NO per-stage confirm-or-change loop. The user sees continuity. HOWEVER, safety fields are
  STILL silently re-derived on load (recomputed from the stored design/materials, no user interaction). For an
  untampered checkpoint of unchanged state this yields the identical result — invisible to the user — so the
  seamless-resume experience is preserved AND SI-4 holds.
- **Portable export/import (UNTRUSTED, user-held):** the modeled restore behavior applies — reset to Scope,
  re-walk with the RESTORE-CONFIRMATION loop (per-stage "still accurate?"), cascade on change. Unchanged from
  the existing design (SI-4 / OM-11 / R*).

THE ONE INVARIANT ACROSS BOTH: safety is ALWAYS computed, NEVER loaded (SI-4). This is a single rule — "safety
is derived, not persisted-as-trusted" — rather than "trust safety from GCS but not from PDF," which is far
harder to get wrong. The difference between the paths is ONLY whether the user is re-walked (no for trusted
GCS, yes for untrusted import); safety re-derivation is on for both. `complete` remains terminal on both paths.

## Status
Settled (✓): DM-1, DM-2, DM-3 (GCS mechanism), the DM-4 principle, DM-5, DM-6, DM-13 (two restore paths).
DEMO SCOPE: the suggested-items store (DM-2 store #3 / DM-12) is DROPPED for the demo — dossier persistence is
the sole focus. It remains a documented forward-looking enhancement (append-only Firestore collection when
built), not part of the demo build.
ALL persistence items now SETTLED: DM-1..DM-11 + DM-13 resolved (DM-4 field→tier table done; DM-7 stable ids;
DM-8 semver reject-on-major; DM-9 broken-ref→re-walk; DM-10 persist-value+recompute; DM-11 no-redaction/
TTL-purge). DM-12 (suggested-items store) remains the ONLY deferred item — dropped from demo, forward-looking
Firestore enhancement. The persistence layer is fully specified and ready for code-engineering.
