# Persona Schema

This directory holds the unified persona-pack schema used by the chat station and the seed-selection flow.

Planned fields:

- `meta.json`
- `intro.md`
- `profile.md`
- `mindset.md`
- `heuristics.md`
- `expression.md`
- `persona_examples.md`
- `state.md`
- `guardrails.md`

Field mapping:

- `WeClone-Skills` informs the split between persona identity, examples, runtime state, and guardrails.
- `nuwa-skill` informs the `mindset`, `heuristics`, and `expression` sections as separate thinking layers.
- `self-skill` informs the future `Work System` and `Reply Persona` structure used by the self-persona entry.

Seed metadata:

- `is_seed` marks whether a persona should appear in the Seed page.
- `seed_source` records the upstream open-source reference used during normalization.
- `seed_group` is the product-facing grouping label shown on Seed.
- `is_featured` and `sort_order` support homepage and seed-page curation.
- `is_favoritable` and `persona_kind` help distinguish published seed personas from future self-persona entries.
