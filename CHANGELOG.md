# Changelog

## V1.2.1 - 2026-04-15

- Added `/persona/admin` as a lightweight admin entry page for LLM configuration.
- Added persona-side `llm_configs` persistence and admin APIs for reading, saving, and activating the default model config.
- Updated the chat gateway to prefer the saved admin configuration before falling back to environment variables.
- Added a frontend admin service and a minimal pastel-styled admin UI.

## V1.2.0 - 2026-04-15

- Added `backend/app/services/prompt_builder.py` to turn persona skill files into structured system prompts.
- Added `backend/app/services/llm_gateway.py` to call an OpenAI-compatible chat API from environment variables.
- Added `backend/app/services/chat_service.py` and `backend/app/routers/chat.py` for real persona chat sessions.
- Added SQLite-backed chat session/message models so the current conversation context can be preserved.
- Replaced the frontend mock reply flow with a real chat API flow in `frontend/src/views/ChatPage.vue`.
- Filled the first two persona skills with `mindset`, `heuristics`, `expression`, `persona_examples`, `state`, and `guardrails` files.

## V1.1.3 - 2026-04-15

- Removed an accidentally committed `frontend/node_modules 2` symlink from the repository.
- Kept the production nginx fix for `app.tokendancer.xyz` intact.

## V1.1.2 - 2026-04-15

- Added an explicit `app.tokendancer.xyz` nginx server block for the persona station.
- Redirected the app root `/` to `/persona/` so the main site no longer falls through to the backend 404.
- Kept the `/persona/` and `/persona-api/` subpath deployment model unchanged.

## V1.1.1 - 2026-04-15

- Unified the repository around the single `frontend/` directory.
- Removed the legacy `xuedingtoken-frontend/` tree from the repository.
- Updated deployment scripts, docs, and status notes to reference the current layout only.
- Kept the `tokendancer.com/persona/` deployment flow intact.

## V1.1.0 - 2026-04-15

- Implemented the persona list/detail interface layer for the current upgrade pass.
- Added `backend/app/services/persona_loader.py` and the persona schema models.
- Added `GET /persona-api/personas` and `GET /persona-api/personas/{slug}`.
- Added two publishable minimal personas under `backend/personas/`.
- Converted the homepage and detail page to fetch persona data from the backend and show loading, empty, and error states.

## V1.0.4 - 2026-04-15

- Added a systemd service unit for the persona backend and updated deployment to install it so the server runs `backend/main.py` instead of the legacy app entrypoint.

## V1.0.3 - 2026-04-15

- Updated the backend deployment script to restart the actual server unit `tokendancer-backend.service`.

## V1.0.2 - 2026-04-15

- Made backend deployment skip legacy Alembic migrations by default so the persona station can be deployed against the current lightweight backend entrypoint.

## V1.0.1 - 2026-04-15

- Fixed the backend deployment script to use the project virtual environment when installing Python dependencies, avoiding the server's externally managed system Python.

## V1.0.0 - 2026-04-15

- Created the initial persona-station scaffold.
- Added repository execution rules in `AGENTS.md`.
- Introduced the subpath-ready frontend skeleton under `frontend/`.
- Added a minimal FastAPI backend entrypoint with `/persona-api/health`.
- Added deployment samples for frontend build, backend deploy, and Nginx routing.
- Added the persona schema, seed, and published persona directories for the V1 workflow.
- Aligned `frontend/tsconfig.node.json` with the installed Vue TypeScript config package so the frontend build passes in this workspace.
