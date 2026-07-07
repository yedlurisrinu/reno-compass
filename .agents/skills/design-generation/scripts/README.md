# Deterministic tools for design-generation
Antigravity implements these at codegen; contracts only here.
- geometry.py — area, volume, clearances to FINISHED surface; validate unit recorded on every dimension; flag implausible dims (do not compute).
- schematic_generator.py — render the labeled block-diagram schematic per design option. NOT-TO-SCALE (to-scale is roadmap); labels each element/zone; SVG output (SVG = roadmap, simple labeled diagram for demo). Writes schematic_ref into the option. Deterministic render — the skill composes the layout, the tool draws it.
- lighting_calc.py — per-room lighting check: fixture output (lumens) vs room/zone area vs the IES target from the lighting-targets skill (JA8 cross-check where CA). Writes lighting_requirements per room into the option (Design computes; Materials READS from dossier — AM-N2). Deterministic table lookup + arithmetic.
