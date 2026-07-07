# Deterministic tools for displacement-alternatives
Antigravity implements these at codegen; contracts only here.
- budget_feasibility.py — Logistics verdict guard: total_with_displacement = refined_estimate(active option) + chosen displacement cost; test vs budget target AND ceiling. Returns {feasible_within_target, feasible_within_ceiling, gap_amount}. Feeds T5/T5a (displacement recalibration loop re-invokes after each optimization step). Deterministic comparison — never a judgment call.
