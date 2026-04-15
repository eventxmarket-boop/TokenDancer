# Changelog

## V1.4.7 - 2026-04-16

- Simplified the homepage subtitle to a single line and made the two central stickers interactive entry points.
- Reworked the Create landing into five collapsible main paths instead of a flat catalog board.
- Cleaned up Create wizard and result page language so they read more like product flows.
- Raised the chat context window from 12 turns to 20 and split out the context assembly entry point for future summarization.

## V1.4.6 - 2026-04-16

- Simplified the homepage subtitle so it now reads as a single concise product statement.
- Kept the homepage layout, stickers, and navigation behavior unchanged while tightening the opening copy.

## V1.4.5 - 2026-04-16

- Reworked the homepage into a minimal entry screen with two central stickers and two primary actions.
- Kept the top-right text navigation visible for Home, Seed, Favorites, Create, and Me.
- Removed the homepage's previous flat content sections so the layout feels more focused and less crowded.
- Tightened the homepage's visual hierarchy so the page reads like an entry point, not a content board.

## V1.4.4 - 2026-04-16

- Cleaned up Create-facing frontend copy so it reads like a normal product page instead of a development screen.
- Removed direct exposure of internal source fields and draft-oriented wording from the Create landing, wizard, and result views.
- Reworked the Create wizard and result page language to emphasize user outcomes, gradual refinement, and finished-looking product entry points.
- Kept the underlying Create flow unchanged while improving the visible product language and presentation.

## V1.4.1 - 2026-04-16

- Reworked the frontend into a more product-like landing experience with stronger visual hierarchy and spacing.
- Split the product into clearer `Seed`, `Create`, and `Favorites` entry pages while keeping recent sessions accessible.
- Upgraded page typography, card rhythm, and hero layouts so the interface feels more intentional and less flat.
- Refined the homepage to emphasize the two core product lines first, then surfaced curated personas and recent sessions.

## V1.4.0 - 2026-04-16

- Added a Seed selection page for browsing normalized persona packs from the curated seed layer.
- Added a Favorites page backed by local browser storage so commonly used personas can be reused quickly.
- Added a Create page that introduces the self-persona flow as Work System plus Reply Persona.
- Reworked the homepage around the two main product lines: creating a self persona and chatting with seeded personas.
- Added seed metadata and source-mapping documentation to clarify how open-source references map to the app's persona-pack model.
- Added two new normalized seed personas, `framework_coach` and `boss_view`, to expand the curated selection set.

## V1.2.5 - 2026-04-15

- Added session detail and latest-session APIs so chat history can be restored after re-entry.
- Changed clear-context behavior to create a fresh session instead of deleting historical records.
- Added backend regression tests for chat history persistence and session reset behavior.
- Tightened the shared persona prompt with stronger answer-quality guidance.

## V1.2.4 - 2026-04-15

- Extracted a shared backend text sanitizer for `<think>`, `<reasoning>`, and `<analysis>` blocks.
- Added regression tests to verify sanitized replies and the no-thinking prompt constraint.
- Kept the frontend display-layer sanitizer in place as a backup guard.

## V1.2.3 - 2026-04-15

- Added backend reply sanitization to remove `<think>`, `<reasoning>`, and `<analysis>` blocks before responses reach the frontend.
- Added a shared frontend message sanitizer as a second display-layer guard.
- Extended the persona system prompt with an explicit "do not output reasoning process" constraint.

## V1.2.2 - 2026-04-15

- Added a dedicated `tokendancer.xyz` nginx entry for the persona station.
- Prepared HTTPS routing so the bare domain can redirect to `/persona/` without hitting the backend 404.
- Kept the existing `app.tokendancer.xyz` deployment unchanged.

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

## V1.3.0 - 2026-04-15

- Deepened the `zhang_xue_feng` and `sun_justin` persona skill packs with richer mindset, heuristics, expression, examples, and guardrails.
- Added a `title` field to `chat_sessions` and generated short titles from the first user message.
- Added `GET /persona-api/sessions/recent` and a new recent sessions page for continuing prior conversations.
- Connected the homepage and Me page to real recent-session data instead of static placeholders.
- Strengthened the shared prompt constraints so replies emphasize judgment order, conditions, tradeoffs, and next steps.

## V1.2.7 - 2026-04-15

- Hid recommended prompts after the first real message so they only appear in an empty conversation.
- Added automatic chat scrolling to the bottom after user messages, assistant replies, and restored history.
- Kept skill, model, and backend chat logic unchanged.

## V1.2.6 - 2026-04-15

- Fixed assistant chat bubble rendering so Markdown now displays as formatted HTML instead of raw `**` text.
- Added a lightweight frontend Markdown renderer for bold text, lists, and paragraph breaks.
- Kept the existing think-block sanitization and session persistence behavior unchanged.

## V1.4.3 - 2026-04-16

- Upgraded Create from a capability catalog into a step-based creation wizard.
- Added self persona, source-based creation, and relationship persona flows.
- Added a wizard result page that shows a structured persona draft and supports local editing.
- Added a backend draft builder and `POST /persona-api/create-wizard/draft`.
- Kept the Create catalog as the upstream capability map for the wizard entry points.

## V1.4.2 - 2026-04-16

- Added a dedicated Create capability catalog for self, source, relationship, digital twin, and protection workflows.
- Exposed `GET /persona-api/create-catalog` for the frontend Create page.
- Rebuilt the Create page into a grouped catalog view with a hero section, functional zones, and sticky selection details.
- Kept Seed limited to ready-made personas while routing creation templates into Create only.
- Added endpoint coverage for the Create catalog response.

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
