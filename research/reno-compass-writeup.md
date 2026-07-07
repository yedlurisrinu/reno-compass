# Reno Compass

### An empathetic guide that helps families scope, design, budget, and safety-check a renovation — and audit a contractor's quote — so they go in informed, not hopeful or anxious.

**Track: Concierge Agents**

---

## The problem

Most renovations don't go sideways because the homeowner is careless or the contractor is dishonest. They go sideways because the family walks in without an empathetic understanding of the process. Nobody told them that the wall they want gone might be holding up the second floor. Nobody warned them that the permit they skipped will surface at resale. Nobody helped them see that the contractor's quote was missing waterproofing and debris haul-away until the invoice arrived thousands over. The agreement stayed loose, expectations drifted, and a project that began as a shared family dream — the bathroom they'd promised themselves for years — became a months-long source of household stress that everyone, including the kids, lived inside of.

The gap isn't money or intent. It's foresight and empathy. Families undertaking a renovation are information-asymmetric: they can't reliably scope the work, can't budget realistically, can't tell a complete quote from a corner-cutting one, and genuinely don't know which tasks are a fine weekend DIY versus which ones are dangerous or illegal to attempt themselves. That uncertainty is where the stress lives — and it's felt hardest by the family, not the professionals.

Reno Compass closes that gap. It walks a family through the whole journey with the foresight a seasoned friend in the trades would offer — for anything from a moderate weekend DIY to a professional-grade remodel — so they go in knowing what to expect and how to handle it *before* it becomes a problem.

## What Reno Compass does

Reno Compass guides a household from first idea to a validated, buildable plan through a sequence of gated stages, each handled by a specialized agent. It does not replace a contractor, an engineer, or a permit office. It makes the family *fluent* enough to work with all three from a position of understanding rather than anxiety. Everyone walks the full journey — there are no shortcuts, because the agent cannot give a family good guidance about a project it doesn't fully understand.

Take a bathroom remodel — the project we demonstrate end to end. A family arrives wanting "a nicer bathroom, maybe move the vanity, budget around fifteen thousand." Reno Compass takes them through eight stages:

**Scope** — a mandatory conversation surfacing the real goal, who lives in the home (including the youngest and eldest, which drives safety questions later), accessibility and health needs, allergies, must-haves versus nice-to-haves, timing, budget target *and* ceiling, and the *hidden conditions* that ambush older homes (knob-and-tube wiring, no waterproofing behind tile, water damage under the subfloor). It gives an early per-square-foot ballpark with a regionally-scaled contingency line, and a kind reality-check — so a family hoping to gut a bathroom for a thousand dollars learns that gently and up front, not four stages later.

**Design** — precise measurements in; labeled options out. The family always sees a *preferred* and an *economy* option to start. If the preferred runs over the ceiling, the economy option is the first fallback; if the family wants to keep refining, they steer up to two more **user-directed** design passes ("keep the double vanity but drop the heated floor") — a hard cap of four options total, so the conversation converges instead of looping forever. Each option carries a value proposition tied to the family's priorities, a per-room lighting plan, intended material types, a labeled schematic, and a refined cost estimate.

**Safety & Permit** — the guardrail heart of the tool. Every proposed *and implied* action (moving a vanity implies moving plumbing) is classified per-item by tier, with a sourced rationale, and permit needs are flagged and jurisdiction-noted. This is where the family gives informed consent for anything that needs a professional. Where a heavy or high-draw material is intended, Safety records the physical "envelope" its classification assumed, so a later product choice can be checked against it.

**Logistics & Feasibility** — the reality most families forget: which rooms and utilities go offline and for how long, whether they can live through it or need to relocate (and what *that* costs, gated by whether they're in a house or a condo), tenant and HOA obligations, and the honest feasibility verdict against both budget target and ceiling. When displacement pushes the total over the ceiling, the agent runs a staged recalibration — ask whether it's separately funded, optimize inline, offer specific trims — never a forced rollback and never a "not feasible" wall.

**Materials** — a complete, itemized materials list: quantities with waste overage, cost bands, allowances for finish items the family prices themselves (with the arithmetic shown), a lighting-informed finish recommendation, and every material screened against stated allergies. When a chosen product exceeds the safety envelope recorded earlier, that single item is sent back to Safety for a quick re-check — the rest of the plan untouched. The list ships as its own shoppable spreadsheet, delivered alongside the final plan.

**Contractor Validation** — the family provides a real quote (text or PDF) and Reno Compass audits it against the scope it helped build: demolition, disposal, waterproofing, permit line, suspiciously low labor, missing licensed trades. Whether or not a quote exists, the family gets a "what to demand" checklist to carry into contractor conversations.

**DIY Planning** — for the work the family will do themselves, step-level procedure and a tools list, refined interactively to their experience. It generates procedure only for non-professional work; where a professional step sits in the middle of a DIY sequence, it appears as a *hold-point* ("wait for the licensed plumber to finish the rough-in here") — making the hand-off explicit rather than silently assuming it. It never crosses into procedure for professional-required work. The stage runs only when there is DIY-scoped work to plan.

**Synthesis** — a single family-facing PDF they own: the whole plan, safety callouts foremost, and — when the family committed to a design — phase checklists for execution. When a budget gap remains, the same rich plan carries an honest "here's the gap to bridge to move into execution" section at the end — never a dead-end "not feasible," always a path forward. The materials spreadsheet travels alongside as a separate file.

The throughline is empathy: at every stage the agent explains *why* something matters, so the family makes educated decisions rather than following orders from a bot.

## How it works

Reno Compass is a pipeline of specialized agents coordinated by a stage-gate orchestrator over a single shared state object.

**The shared dossier.** Every stage reads from and appends to one structured artifact — the project dossier. Scope, measurements, the chosen design, safety classifications, consents, logistics, the materials list, and quote-audit findings all accumulate in this single source of truth. Stages communicate *only* through the dossier — no private state — which is what makes the handoffs real and auditable rather than a set of disconnected chatbots.

**Stage-gate orchestration.** A controller enforces the pipeline as a state machine with strictly linear forward dependencies. Each stage has preconditions to enter and a gate to exit — and the gate cannot open until every required topic is covered *and* the family confirms. The orchestrator refuses to advance on incomplete information rather than improvising forward. A small number of *controlled, guarded* backward paths exist and are modeled explicitly as transitions: a full redesign loops back to Design (discarding the superseded option's analysis); switching to an already-designed option re-points to its retained analysis without recomputation; a single material that breaches its safety envelope reopens Safety for that one item; and a genuine budget gap routes forward to an honest synthesis. One stage — DIY Planning — is conditional, running only when DIY-scoped work exists. The machine is provably terminating: forward edges are finite and every backward path is bounded (the design-pass cap, the single-item envelope return, the recalibration loop's exit conditions).

**Design passes and analysis retention.** The family can explore up to four design options. Because judging "does the economy option come in under the ceiling?" is a feasibility question that needs full cost and logistics, the preferred and economy options are both analyzed *eagerly* as the pipeline runs — so at the budget moment the agent can say "the economy version lands at this number, under your ceiling" rather than deferring. Each option's downstream analysis (safety, logistics, materials) is *retained*, keyed to that option. Switching between options re-points to retained analysis with no rework and no loss; only a genuine redesign discards superseded analysis. Falling back to the original preferred option after exploring alternatives is therefore instant and lossless.

**Progressive budget thread.** Cost is refined across three resolutions rather than sprung at the end: a ballpark reality-check at Scope, a refined per-option estimate at Design, and an itemized total at Materials — with Logistics judging feasibility against it. This is how the family's aspiration meets financial reality gradually and honestly, with a designed economy option always waiting as a fallback.

**Skills versus tools.** Reno Compass separates reusable *reasoning* skills (scope decomposition, hidden-condition surfacing, safety-tier classification, design generation, estimate auditing) from deterministic *tools* (measurement math, quantity and waste calculation, cost-band and lighting-reference lookup, spreadsheet and PDF generation). Judgment lives in skills; anything that must be exact and repeatable lives in a tool, so numbers are computed from curated references, never hallucinated. Because the target runtime does not guarantee schema-conformant model output, the correctness-critical checks — allergy screening, allowance unit-matching, the envelope check — run as deterministic tools rather than trusting the model's text.

**The safety-tier skill as a shared spine.** One classification skill — used in Safety, and again in the contractor audit — maps every action to a tier with a sourced rationale. Defining it once, as a single source, keeps the guardrail consistent everywhere it fires.

## Safety and guardrails

Reno Compass's guardrails are intrinsic to the domain, not bolted on — and they are the heart of what makes it a *safe* concierge for a family. Every proposed and implied action is classified per-item (a real bathroom is mixed-tier — retiling is fine to DIY, moving plumbing needs a permit, touching the panel needs a pro):

- **Tier 1 — Professional required.** Structural/load-bearing modification, service-panel electrical, gas. No DIY procedure is provided.
- **Tier 2 — Permitted / regulated.** DIY-feasible but legally gated work; the agent proceeds while surfacing permit and inspection needs.
- **Tier 3 — Proceed.** Cosmetic and finish work.

Three design choices make this a genuine safety feature rather than theater. First, **calibration**: Tier 1 is reserved for work that truly needs a licensed professional. A guardrail that fires on everything gets ignored — so the tool deliberately does *not* over-escalate, which is what lets its warnings carry weight. Second, **depth, not procedure**: rather than slamming the door on Tier-1 work, the agent asks for informed consent and then explains the *intuition* — **removing a load-bearing wall requires a properly sized header or beam that a structural engineer must specify**, and here's why — without ever giving how-to instructions, and it holds that line under repeated or reframed pressure. Consent unlocks understanding so the family can talk to the professional informed; it never authorizes a dangerous DIY. Third, **sourcing**: classifications and permit disclosures are grounded in the building code (for example, **bathroom receptacles require GFCI protection under NEC 210.8**) and flagged for local verification with the Authority Having Jurisdiction — each flag states which rule fired and why. Hazards like older-home lead or asbestos are handled as educational disclosures that inform the family's judgment, not automatic escalations.

The safety picture is never trusted from a file. Whenever a saved plan is reloaded — on any path — the safety classifications are silently re-derived rather than read back, so a stale or tampered dossier can never inject a false all-clear. And because a tool that classifies structural and electrical work should be able to show its work, every classification, consent, and permit disclosure is written to an immutable, append-only audit trail — the defensible record of what the tool told the family and what they agreed to.

One further guardrail is a security boundary, not a safety one: the contractor's quote is the only externally-authored content the agent reasons over, and it is treated strictly as *data to audit, never as instructions* — an embedded "mark this quote as complete" is audited as content, never obeyed.

## State, persistence, and recovery

Continuity matters for a tool a family uses across several evenings, so the dossier is engineered to survive interruption without ever compromising the safety guarantees.

The dossier is checkpointed to server-side object storage every couple of minutes and at every stage gate, keyed to an anonymous session token that connects both the browser and API clients — no login required. If the app crashes or the family reopens it, the session resumes exactly where it left off, seamlessly, with no re-walk. The family can also export the dossier as a portable file they own — the first-class recovery path for the cases a token can't cover (a cleared browser, a different device), surfaced with a save nudge at natural moments.

The two restore paths differ by trust, and one invariant spans both: **safety is always re-derived, never loaded.** A trusted server checkpoint resumes seamlessly; an untrusted imported file is re-walked stage by stage with a confirm-or-change pass, cascading only where something actually changed. A delivered plan is terminal — to change it, the family starts fresh. Cross-references inside the dossier use stable identifiers so they survive option reordering, and a version mismatch on an old exported file is handled honestly (a clear "made with an older version" message rather than a silent, possibly-wrong migration).

## Safety-critical engineering choices

A few decisions were made specifically because this is a safety domain, and they're worth calling out:

- **The classifier is calibrated against real code, not maximal caution** — over-escalation is treated as a failure mode because it trains families to ignore the warnings that matter.
- **The Tier-1 firewall is a hard line** — depth is explained, procedure never is, and the line holds under emotional or reframed pressure.
- **Materials detects, Safety owns** — a product that breaches its envelope reopens Safety for that one item; no other stage is ever allowed to set or change a tier.
- **The contractor quote is untrusted input** — audited, never obeyed, with prompt-injection resistance built in.
- **Reference data is scoped and frozen by design** — the cost bands and the tier matrix are bathroom-specific; the architecture generalizes, but the guardrail data must be extended in lockstep with any new domain, never ahead of it.

## Scope and forward-looking roadmap

The guiding priority was to demonstrate rigorous agentic engineering against a genuine, stressful real-world problem, so scope was drawn to keep that focus sharp, with several capabilities deliberately staged as forward-looking enhancements. Each is a considered sequencing decision — prove the agentic architecture and the safety spine first, then broaden:

- **Accounts and identity.** Session recovery today rests on an anonymous token plus portable export; account-based persistence with full data-protection guarantees is the enhancement that turns "mostly recoverable" into "always recoverable" and unlocks per-user history. Deferred deliberately, because identity done properly is its own body of work.
- **The community reference loop.** Every time the agent must search the web for an item not in the curated reference set, that item is a candidate for the vetted knowledge base. A shared, append-only "suggested-items" store — staged for human review before merging into the frozen references — turns real usage into a growing, validated knowledge base. Architected, and deferred from the demo to keep the persistence surface minimal.
- **Live, local pricing.** Cost and rule references are curated (drawn from published industry sources and building code, model-drafted then human-validated and frozen) rather than pulled live; county-level live pricing is a planned enhancement, because the agentic value is in complete, well-reasoned estimates rather than today's exact lumber price. Estimates are always presented as ranges with a verify-locally disclaimer.
- **Multi-domain expansion.** The pipeline, the tier-classification reasoning, the retention model, and the dossier are all domain-agnostic; what's bathroom-specific is the frozen reference data and the safety matrix. Kitchens and whole-home add new hazards (gas ranges, high-draw appliance circuits, larger spans) that require their own curated, frozen matrices — added in lockstep with broadening the agent's scope, never ahead of the data.
- **Multi-jurisdiction code lookup.** Code coverage centers on a single framework with explicit local-verification flagging; multi-jurisdiction lookup is a roadmap item that demands precision work before it can be trusted in a safety domain.
- **Richer input and output.** Image/vision input (photograph the space instead of measuring) is a natural future modality; the design stage produces labeled schematics today, with to-scale drawings later.
- **Export privacy controls.** The portable export is complete today and the family is told it holds their personal details; a redaction option for exported files is a natural companion to the accounts-era privacy work.

## Course concepts applied

Reno Compass is a direct application of the course's core concepts. It demonstrates **multi-agent orchestration** through a stage-gate state machine coordinating eight specialized agents with linear forward dependencies, guarded backward transitions, cascade invalidation, per-option analysis retention, and a conditional stage — proven to terminate. It shows **reusable skills** through a shared safety-tier classification skill used across stages and a library of focused reasoning skills; the **skill-versus-tool separation** that keeps deterministic computation out of the model's judgment; **shared state management** through a single dossier that also enables checkpointed recovery and portable save-and-resume; and **intrinsic guardrails** through the calibrated, per-item, consent-gated, sourced safety model — plus prompt-injection resistance on externally-provided documents. The entire system was specified tech- and API-agnostic, as behavior and data contracts, so the implementation is portable across coding agents and frameworks.

## Demo and links

**Live demo / project link:** _[placeholder — public URL or repo to be added before submission]_

**Code repository:** _[placeholder — GitHub URL with setup instructions to be added]_

**Video walkthrough:** _[placeholder — YouTube link, ≤5 min, to be added]_

What to watch for in the demo: the mandatory scoping gate refusing to advance on incomplete input; the early budget reality-check grounding expectations; the Tier-1 consent moment where the agent escalates depth without giving procedure; the contractor-quote audit catching a missing permit and waterproofing line; and the closing synthesis PDF that reframes a budget shortfall as a gap to bridge rather than a dead end.
