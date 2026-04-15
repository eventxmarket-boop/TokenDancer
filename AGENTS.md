# Codex Execution Rules

This repository is the home for the `tokendancer-persona-station` persona web app.

Hard rules:

1. Versioning is strictly monotonic.
   - Start at `V1.0.0`.
   - Only move forward: `V1.0.1`, `V1.0.2`, `V1.1.0`, and so on.
   - Do not rename versions or jump backwards.

2. Every change must update both `VERSION` and `CHANGELOG.md`.
   - If code changes, version and changelog must move with it.
   - `VERSION` contains a single line only.

3. Frontend must support subpath deployment.
   - Vite base must stay `/persona/`.
   - Router history must be created from the Vite base.
   - Static assets and refreshes must work under `/persona/`.

4. Backend APIs must stay under `/persona-api/`.
   - Do not mix `/api/` and `/persona-api/`.
   - New persona endpoints must use the persona API prefix consistently.

5. External persona sources must go through `seed_personas/` first.
   - Do not publish third-party `SKILL.md` files directly.
   - Import, normalize, and then promote into `personas/`.

6. V1 does not include training or long-term memory.
   - No fine-tuning.
   - No vector search.
   - No persistent memory beyond the current conversational context.
   - Anything in that direction belongs to V2.

7. Keep the product boundary narrow.
   - First release is the official persona showcase and chat station.
   - Avoid expanding into a training platform or user-generated persona platform in V1.

Source mapping for this repository:

- `mliu98/awesome-human-distillation`
  - Use as the selection index only.
  - Treat it as a catalog of persona directions, not a runtime dependency.
  - The Create catalog should be derived from it as a product curation map, not as published Seed personas.
- `xming521/WeClone-Skills`
  - Use as the persona-pack structure reference.
  - Keep persona, context, and review boundaries separate.
- `alchaincyf/nuwa-skill`
  - Use as the extraction template for mindset, heuristics, and expression DNA.
  - Focus on how a persona thinks, not just how it speaks.
- `moyitech/self-skill`
  - Use as the product entry reference for creating a self persona.
  - The first-stage structure is `Work System` plus `Reply Persona`.

8. Preserve the current worktree.
   - Do not revert unrelated edits.
   - Do not delete legacy directories unless explicitly asked.
   - The active frontend root is `frontend/`; do not reintroduce the legacy frontend tree as a live source tree.

Execution preference:

- Favor small, shippable increments.
- Keep the frontend and backend aligned with the current stage.
- When introducing new files, follow the repository structure described in the persona workflow.
