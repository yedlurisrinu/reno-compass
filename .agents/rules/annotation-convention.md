# Rule — Annotation Convention

Always-active. How the dossier schema signals attention to the agent (SI-28).

- Use the annotation vocabulary as first-class field tags: `[safety]`, `[SENSITIVE]`, `[computed]`,
  `[narrative]`, `[user]`, `[SECURITY]`.
- On high-attention fields, add a short imperative consequence phrase — tell the agent what to DO, not just
  that the field matters. E.g. "SHAPES design", "MUST screen against these", "re-derived on restore".
- Point to the full rule via the source note (`see SI-n` / constitution principle).
- Annotations STEER (soft guidance). For must-not-fail cases, a CODE validation check is added too
  (belt + suspenders) — see the code-level validations bundled as skill scripts. Annotation alone is never the
  guarantee for a safety- or number-critical field.
