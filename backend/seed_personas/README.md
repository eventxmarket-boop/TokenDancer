# Seed Personas

This directory is the staging area for imported third-party persona sources before they are promoted into `backend/personas/`.

Rules:

- Normalize external sources here first.
- Do not publish external `SKILL.md` files directly.
- Keep the seed layer separate from the published persona layer.
- Use this directory for normalized source material, not for direct runtime exposure.
- The public `Seed` page should only surface personas that have already been normalized into the app's persona-pack format.
- Seed metadata should be explicit: `is_seed`, `seed_source`, `seed_group`, `is_featured`, `is_favoritable`, and `persona_kind` must be filled before promotion.
