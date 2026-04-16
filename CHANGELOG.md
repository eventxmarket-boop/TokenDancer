# Changelog

## V1.4.38 - 2026-04-16

- Raised the Me page Favorites card to the same interaction stack as the other entries so it no longer feels inert.
- Moved stacking priority to the link layer and added a clearer press state for all three Me page cards.
- Preserved the existing semi-overlapped design while making the middle card easier to hover and click.

## V1.4.37 - 2026-04-16

- Increased the Me page card lift and selection responsiveness so the active card appears on top more clearly.
- Added faster pointer-triggered highlighting for all three personal-center cards, including Favorites.
- Kept the semi-overlapped pattern but made the hover/selection motion more immediate and visible.

## V1.4.36 - 2026-04-16

- Raised the active personal-center card to the top of the stack so the selected entry is easier to inspect.
- Kept the semi-overlapped Me page layout while improving z-index behavior on hover and selection.
- Preserved the existing product scope and only adjusted the front-end interaction polish.

## V1.4.35 - 2026-04-16

- Restyled the personal center cards into a semi-overlapped stack that matches the homepage sticker pattern.
- Added hover and active color feedback so the three entry cards feel clickable and responsive.
- Kept the personal center focused on the three real entries without changing backend behavior.

## V1.4.34 - 2026-04-16

- Added the minimal auth closure with login and register pages.
- Added JWT-backed register/login/me endpoints and frontend auth-state persistence.
- Protected user-scoped pages so My Seeds, Favorites, and Sessions resolve against the signed-in user.
- Kept the create-to-save flow redirecting to login when the user tries to persist a seed while signed out.

## V1.4.33 - 2026-04-16

- Fixed the frontend type definitions so family companion `family_subtype` is accepted by the create wizard and my-seeds / result surfaces.
- Kept the self-persona display normalization in place so the create flow continues to show `自我主线` instead of reintroducing `我的人格`.
- This is a follow-up deployment fix after the `V1.4.32` UI label cleanup.

## V1.4.32 - 2026-04-16

- Unified the visible self-persona display labels across the create flow so the first-load UI no longer reintroduces `我的人格` from query defaults or older saved labels.
- Normalized self persona display names to `自我主线` in the wizard, result page, and my-seeds surface to keep the entry wording consistent.
- Kept the first-load cache behavior aligned with the current UI shell and no-cache strategy.

## V1.4.31 - 2026-04-16

- Fixed the first-load stale UI issue by setting `/persona/` and `/persona/index.html` to `no-store` while keeping hashed assets cacheable.
- Simplified the visible self-persona create path so `我的人格` is shown as a single entry instead of repeating multiple times.
- Renamed the top navigation `我的` entry to `个人` to reduce repeated wording in the shell chrome.
- Kept the UI polish focused on front-end structure and cache behavior without changing backend persona logic.

## V1.4.30 - 2026-04-16

- Further reduced duplicate self-persona wording in the Create flow so only one visible `我的人格` entry remains.
- Moved the Seed featured recommendations out of the top-right sidebar and made them expand below the main list via `精选推荐 / 收起`.
- Removed internal version/source/status disclosures from persona detail, favorites, and recent-session surfaces.
- Improved my-page centering, card hover feedback, and global night-mode placeholder readability.
- Kept all UI changes frontend-only and aligned the visible labels to Chinese.

## V1.4.29 - 2026-04-16

- Optimized the frontend interaction and style polish across the wizard, Seed, my page, and create surfaces.
- Improved placeholder readability in forms and kept night-mode text contrast easier to read.
- Centered the my-page cards and unified their text alignment.
- Normalized create-page wording around `我的人格` and removed repeated mixed-language labels from the display layer.
- Made Seed recommendations collapsed by default with a working `预览 / 收起` interaction.
- Kept Seed category pills and labels from exposing raw slug-like internal identifiers.

## V1.4.28 - 2026-04-16

- 收口 Create 向导页、首页、Seed 页、我的页中的开发中间态说明。
- 删除无实际意义的解释文案与状态说明。
- 首页品牌区支持点击返回主页，顶部不再展示“人格小屋”。
- Seed 卡片改为只显示人格名字，不再展示 skill slug。
- Seed 页统计贴片支持点击跳转到对应区块。
- 整体优化前台信息密度与页面整洁度。

## V1.4.27 - 2026-04-16

- Fixed the family-companion wizard so the material input layer is rendered directly in the template.
- Exposed family chat-history, memory-notes, text-material, image-note, and voice-note fields as visible controls.
- Added explicit family uploaded-file listing and delete actions in the wizard template.
- Kept family raw-material submission and result summaries aligned with the same persisted object.
- Strengthened family create and my-seeds regression coverage for raw-material round-tripping.

## V1.4.26 - 2026-04-16

- Fixed the family-companion wizard so the material input layer is visible in the frontend template.
- Added visible family material controls for chat history, memory notes, text materials, and uploaded text files.
- Ensured family draft submission writes raw materials through the frontend payload.
- Surfaced material extraction summaries in the Create result view so users can see what was distilled.
- Strengthened create and my-seeds regression coverage for family raw-material round-tripping.

## V1.4.25 - 2026-04-16

- Made the family-companion path explicitly carry extracted emotion rules alongside persona and memory data.
- Added a dedicated family material-to-memory extraction helper so raw materials are converted into a structured memory base before saving.
- Surfaced family emotion-rule summaries in the Create result and created-seed summary flow.
- Ensured family chat context consumes persona profile, memory base, and emotion rules together.

## V1.4.24 - 2026-04-16

- Expanded the intimate-relationship Create paths so they can ingest pasted materials and uploaded text documents instead of relying only on hand-filled fields.
- Added raw material payloads for intimate drafts so the backend can derive interaction samples, relationship memory, style samples, and candidate reply cues from chat history and text materials.
- Surfaced concise material-input summaries in the Create result and My Seeds flows while keeping the full raw materials hidden from the user-facing cards.
- Kept the intimate save/open/chat chain aligned around the same persisted object across the four main paths.

## V1.4.23 - 2026-04-16

- Expanded the family-companion and reunion create flows so they can ingest pasted materials and uploaded text documents instead of relying only on hand-filled fields.
- Added raw material payloads for family and reunion drafts so the backend can derive memory bases from chat history, memory notes, diary entries, letters, and text documents.
- Surfaced concise material-input summaries in the Create result and My Seeds flows while keeping the full raw materials hidden from the user-facing cards.
- Kept the family and reunion save/open/chat chain aligned around the same persisted object.

## V1.4.22 - 2026-04-16

- Added explicit source URL checks for the intimate relationship create paths.
- Kept the intimate Create catalog normalized around the four main paths while preserving precise upstream repository mapping.
- Added regression coverage to make sure the intimate catalog entries keep their source URLs aligned with `relationship-training-skill`, `xinyi`, `crush-skill`, `partner-skill`, `npy-skill`, `ex-skill`, `first-love-skill`, and `shuixian-skill`.

## V1.4.21 - 2026-04-16

- Normalized the family relationship Create flow around `family_companion` and `reunion_persona` with explicit upstream source URLs.
- Kept `parents-skills`, `MamaSkill`, and `reunion-skill` as the normalized family mapping sources in the Create catalog.
- Expanded the family and reunion wizard payloads to include persona, memory, and material layers.
- Added dedicated family and reunion services to keep save, open, and chat aligned with the same persisted object.
- Updated create and seed round-trip coverage for the new family/reunion chain.
## V1.4.20 - 2026-04-16

- Consolidated the family relation Create path around `家人陪伴` and `重逢人格` with explicit upstream source mapping.
- Kept `parents-skills`, `MamaSkill`, and `reunion-skill` as the normalized family mapping sources in the Create catalog.
- Expanded the Create wizard, result page, and My Seeds flow to surface reunion personas as a distinct family path.
- Added regression coverage for the family and reunion create/save/open/chat round trips.

## V1.4.19 - 2026-04-16

- Unified the four self-persona Create entries into a single `我的人格` main line.
- Added the shared five-layer self-persona structure: `work_system`, `reply_persona`, `thinking_dna`, `memory_evidence`, and `reflection_rules`.
- Aligned Create, result, My Seeds, and chat flows around the same self persona object.
- Added support for handwritten input, pasted text, and plain-text file evidence in the unified self-persona path.

## V1.4.16 - 2026-04-16

- Added an internal rolling summary for chat sessions so long conversations can retain earlier context without exposing it in the frontend.
- Injected session summary into the model prompt before recent turns, while keeping recent messages intact.
- Reserved a future retrieval hook for older message snippets without enabling any user-facing summary UI.

## V1.4.15 - 2026-04-16

- Switched the `zhang_xue_feng` research provider to a Baidu-first flow for Chinese education scenarios.
- Added Chinese education query normalization, results ranking, and concise facts-summary generation.
- Kept `stub`, `baidu`, and `custom` provider modes while removing DuckDuckGo from the primary path.
- Strengthened official-source priority and graceful fallback behavior when research returns no reliable facts.

## V1.4.14 - 2026-04-16

- Added a research-first split for the `zhang_xue_feng` persona so education and career questions can be classified before answering.
- Introduced `zhangxuefeng_research` as a lightweight research layer for fact-required and hybrid questions.
- Expanded Zhang Xuefeng examples with research-oriented cases that show what should be checked before answering.
- Strengthened guardrails so the persona does not pretend to have checked facts it has not actually researched.

## V1.4.13 - 2026-04-16

- Enhanced the built-in `zhang_xue_feng` persona by absorbing the stronger research framing and decision logic from the open-source skill.
- Expanded `mindset`, `heuristics`, `expression`, `persona_examples`, and `guardrails` to emphasize practical education and job-path judgment.
- Added a prompt-level reminder to keep education and career answers anchored in conditions, exit paths, and tradeoffs.

## V1.4.12 - 2026-04-16

- Added a created-seed fallback to `/persona-api/personas/{slug}` so saved seeds can open like formal personas.
- Kept chat resolution dual-source aware so created seeds can enter the same chat flow as built-in personas.
- Added regression coverage for created-seed detail lookup and created-seed chat entry.

## V1.4.11 - 2026-04-16

- Aligned the Create chain so entry cards, wizard initialization, form schema, and generated results all point to the same creation object.
- Standardized Create navigation payloads with `create_type`, `group`, `source_repo`, `display_name`, `input_mode`, and `schema_key`.
- Prioritized query params over local wizard snapshots so a newly clicked Create card no longer reuses stale state.
- Completed the my-seeds save/list/detail persistence loop so saved creations can be reopened and used consistently.

## V1.4.10 - 2026-04-16

- Fixed Create wizard state pollution by prioritizing entry query params and honoring the reset flag before restoring any local snapshot.
- Added `source_repo` to Create entry navigation so the selected source metadata stays aligned with the chosen card.
- Completed the my-seeds backend round trip by committing create and update mutations before returning.
- Added a regression test that verifies Create -> save -> list -> detail keeps the same persisted persona payload.

## V1.4.9 - 2026-04-16

- Added a day/night theme toggle to the global shell and persisted the choice in local storage.
- Simplified the My page into three direct entry cards: created seeds, favorites, and recent sessions.
- Added a dedicated My Seeds page so saved create results can be reopened, continued, and chatted with consistently.
- Persisted Create wizard results into the backend so the created object can be reopened as the same persona later.

## V1.4.8 - 2026-04-16

- Simplified the Favorites page so it now keeps only the core list, actions, and empty state.
- Removed the self-explaining hero copy, statistics, and product commentary from Favorites.
- Moved the Favorites content upward and centered the list-focused layout.

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

## V1.4.17
- 合并父母人格与妈妈人格为统一的家人陪伴路径
- 吸收 MamaSkill 的 Persona + Memory Base 双层结构
- 新增家庭陪伴专属运行逻辑：情绪判断、记忆提取、温度回复
- 将 darwin 风格的评估与回滚思路纳入家庭人格优化骨架
- 收口家庭关系类 Create 路径，避免重复入口

## V1.4.18 - 2026-04-16

- Prioritized the family and intimate relation Create paths as the first fully usable chains.
- Unified intimate relation creation into four main paths: relation understanding, message simulation, relationship maintenance, and past relation mirror.
- Expanded the family companion and intimate companion creation flows with explicit profile and memory layers.
- Started merging the four self-related Create entries into a later unified main line.

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
