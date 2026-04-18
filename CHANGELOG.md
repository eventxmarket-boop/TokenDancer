## V1.4.125 - 2026-04-19

- Retinted the new `SeedMind` header logo so its displayed palette now aligns with the site’s day-mode accent colors instead of keeping the original blue-purple artwork tones.

## V1.4.124 - 2026-04-18

- Merged the top navigation into `Seed` + `Mind`, renamed the brand to `SeedMind`, and replaced the old text logo with the new uploaded mark while keeping the frontend subpath-safe under `/persona/`.
- Simplified the `我该怎么做` entry UI by removing the extra hero block, trimming redundant cast instructions, freezing the displayed category after each cast, and adding local history + favorite controls for saved hexagrams and chat records.
- Added local `我该怎么做` history visibility to both `收藏` and `个人` pages so favorite hexagrams can be revisited alongside existing persona favorites.
- Tightened night-mode polish by making sticker-style cards darker and making top-right navigation pills round and visually consistent.

## V1.4.123 - 2026-04-18

- Renamed the `健康事务` divination bucket to `健康和日常事务` in the frontend so the category better covers health, disputes, lost-item, and other everyday practical asks.
- Added a first-two-replies soft guidance nudge for `我该怎么做`: within the first two assistant answers only, there is now a 50% chance to append a short variable sentence inviting the user to补更多细节 for a tighter follow-up reading.
- Tightened the `我该怎么做` answer guard so high-coverage categories are no longer misclassified as invalid just for being concise, while still rejecting true empty-shell template answers.

## V1.4.122 - 2026-04-18

- Synced `我该怎么做` frontend question guidance with the selected category bucket so the main textarea placeholder and helper copy now change by大类, making it clearer how to ask travel, study, money, relationship, family, health, and deal questions.
- Added a relevance guard for `我该怎么做` answers so when a high-coverage category still produces a generic empty template, the runtime now rejects it, pulls an adaptive联网语境补充, and forces one stricter rewrite instead of returning an invalid answer.
- Fixed follow-up cleanup so removing the trailing反问 no longer accidentally deletes the entire last paragraph of a continued answer.

## V1.4.121 - 2026-04-18

- Fixed recurring `我该怎么做` answer truncation by preserving model `finish_reason`, detecting length-cut responses, and automatically requesting one continuation pass when the first reply stops mid-thought.
- Changed the closing follow-up question behavior so only the first three divination replies may end with a延伸反问, using a 60% probability, and all replies from the fourth turn onward now end cleanly without反问.

## V1.4.120 - 2026-04-18

- Reworked `我该怎么做` category selection into a two-level frontend flow so users now choose a broad bucket first and then a specific category, making the divination entry less crowded on mobile and desktop.
- Added fixed answer skeletons per divination bucket so replies now stay shorter, use a steadier术语风格, follow the same symbol / relation / state reasoning frame, and end with a natural follow-up question.

## V1.4.119 - 2026-04-18

- Completed backend routing coverage for the current `我该怎么做` frontend category set so all existing categories except `其他` now resolve to a dedicated divination interpretation bucket instead of falling back to the generic path.
- Added regression coverage to guarantee the shipped category list stays mapped and usable before future changes are deployed.

## V1.4.118 - 2026-04-18

- Upgraded `我该怎么做` around a deeper symbol / relation / state framework so model answers now analyze the hexagram as a structured system before mapping it onto the user’s question.
- Added low-coverage question detection and adaptive web-research escalation so when a user asks something outside the current built-in divination buckets, the runtime now falls back to hexagram-first reasoning plus联网背景补充 instead of forcing the wrong template.

## V1.4.117 - 2026-04-18

- Tightened `我该怎么做` question routing with a dedicated lost-item / direction path so方位类问题 now carry trigram-direction grounding instead of falling back to generic divination talk.
- Added answer-contract guards for binary questions and follow-up continuation so the model now gives direct yes/no倾向 earlier, avoids repeating full prior answers on `继续`, and keeps responses shorter and more on-target.

## V1.4.116 - 2026-04-18

- Rebuilt the `我该怎么做` interpretation protocol around a two-layer framework: first analyze the hexagram as a symbol system, then map its dynamics onto the user’s actual question.
- Added structured protocol fields for symbol parsing, relation modeling, core-conflict extraction, and time evolution so model answers now follow a clearer analysis pipeline before giving conclusions.

## V1.4.115 - 2026-04-18

- Added a deep web-research layer to `我该怎么做` so cast answers and follow-up divination chat can now pull in external date, calendar, timing, and factual context before the model replies.
- Kept the new networking layer isolated from the core hexagram runtime by introducing a dedicated `how_to_do_research` service and only passing summarized research context into prompts.

## V1.4.114 - 2026-04-18

- Added a structured divination interpretation protocol to `我该怎么做` so model prompts now classify the question type first, force cast-time alignment, and anchor answers around the most relevant hexagram relationships instead of generic free-form output.
- Added internal focus routing for short trades, general money questions, relationship asks, work matters, disputes, and stay-or-leave questions so the same hexagram can be interpreted with the right emphasis.

## V1.4.113 - 2026-04-18

- Tightened `我该怎么做` divination answers so first replies and follow-up chat now use a more grounded 解卦师 tone, lean more toward安抚, and stay scoped to the current hexagram instead of drifting into generic advice.
- Added output cleanup for `我该怎么做` so model replies no longer leak markdown markers like `**` or heading syntax into the UI.

## V1.4.112 - 2026-04-18

- Added a continuing chat layer to `我该怎么做` so starting a divination now returns a direct model answer immediately and follow-up questions continue against the same hexagram context and chat history.

## V1.4.111 - 2026-04-18

- Changed `随机摇卦` and `在线起卦` from equal four-way random selection to the real three-coin probability mapping so line values now follow the traditional 0/1/2/3 背 -> 6/7/8/9 distribution.

## V1.4.110 - 2026-04-18

- Removed the `太极丸起卦` mode so the liu-yao page now keeps only `随机摇卦`、`手动输入`、`在线起卦`, and cleared the remaining taiji-specific labels from the frontend and backend contract.

## V1.4.109 - 2026-04-18

- Simplified `在线起卦` to a single true-random trigger so each click now emits the next yao in order until all six lines are complete, then the existing cast action can generate the hexagram.

## V1.4.108 - 2026-04-18

- Rebuilt `在线起卦` into a six-step random draw flow so each yao now has its own `开始起卦` trigger, uses true browser randomness to pick one of four line types, and waits for all six draws before casting.

## V1.4.107 - 2026-04-18

- Added an `在线起卦` entry after `太极丸起卦`, reusing the existing manual-entry UI and manual cast flow without changing the underlying liu-yao runtime.

## V1.4.106 - 2026-04-18

- Updated the manual liu-yao input dropdown to use source-style 少阴 / 少阳 / 老阴 / 老阳 labels with背字说明 and removed the raw 6/7/8/9 option text.

## V1.4.105 - 2026-04-18

- Added yao-line previews to manual liu-yao entry so each of the six manual selections now shows its bar shape and moving-line `o/x` marker while entering from bottom to top.
- Reworked the liu-yao board from a horizontal row grid into stacked vertical hexagram columns, with `上爻` at the top and `初爻` at the bottom for both the main and transformed hexagrams.
- Changed the manual-entry result label back to `硬币 / 太极丸起卦` to match the source flow it represents.

## V1.4.104 - 2026-04-18

- Corrected the liu-yao board subtitle for `地雷复` so it now displays `坤·六合` instead of the wrong `坤·一世`.
- Kept the underlying 世应 mapping unchanged while fixing only the visible title tag.

## V1.4.103 - 2026-04-18

- Bound liu-yao cast results to the user-entered cast time so the displayed time,干支, and 旬空 now follow the selected起卦时间 instead of the server clock.
- Replaced the merged cast-mode label with exact mode text such as `硬币起卦` and `太极丸起卦`.
- Switched shensha output to rule-based generation from the cast time and day stem/branch instead of seed-derived mock values.

## V1.4.102 - 2026-04-18

- Replaced the fake liu-yao line-detail generation with palace-based 纳甲/六亲 calculation so visible relations and stem-branches no longer repeat in a fixed mock order.
- Fixed transformed-hexagram generation to flip only moving lines instead of inverting all six lines, and aligned the board bars with each line's real yin-yang value.

## V1.4.101 - 2026-04-18

- Switched liu-yao random casting to true system randomness so repeated casts no longer reuse a seed-derived pseudo-random result.
- Kept `cast_seed` only as the displayed cast time input while leaving manual input and the rest of the board logic unchanged.

## V1.4.100 - 2026-04-18

- Adjusted each liu-yao row to horizontal layout so entries now read like `父母甲巳 ▅ ▅`.
- Moved `↑伏...` onto its own line below the bars for both the main and transformed hexagrams.

## V1.4.99 - 2026-04-18

- Switched transformed-hexagram titles to full names such as `水泽节（坎·一世）` instead of the shortened trigram-only label.
- Removed `纳音` from the liu-yao board display while keeping the rest of the board layout unchanged.

## V1.4.98 - 2026-04-18

- Reworked the liu-yao board UI into a single aligned sheet so 六神、主卦、变卦、世应、`o/x` render as one whole instead of per-line cards.
- Kept the existing cast logic intact while changing only the board presentation.

## V1.4.97 - 2026-04-18

- Removed the `数字起卦` cast mode from `我该怎么做` so the board now only exposes the remaining cast paths.
- Kept the six-yao board, main/transformed hexagrams, and the existing time-based layout intact.

## V1.4.96 - 2026-04-18

- Added proper `世/应` markers to the liu-yao board based on hexagram tag mapping.
- Added changing-line `o/x` markers so moving lines are rendered like the source board.
- Kept the main and transformed hexagrams aligned in a single frame with the source-style board layout.

## V1.4.95 - 2026-04-18

- Removed the duplicate transformed-hexagram title from the top header and kept only the right-aligned title within the transformed board.
- Preserved the main and transformed hexagrams in one aligned frame while keeping the board source-like.

## V1.4.90 - 2026-04-18

- Added the transformed hexagram board to `我该怎么做` so changing lines now render a second hexagram panel instead of only the main one.
- Kept the board layout source-like while filling the missing变卦 section that was previously only present in raw data.

## V1.4.89 - 2026-04-18

- Removed more non-source liu-yao extras from `我该怎么做` so the board stays closer to the referenced layout.
- Removed the separate detail and song-add routes from the visible router so the module no longer exposes extra surfaces.
- Corrected the panel title ordering to better match the source-style hexagram name presentation.

## V1.4.88 - 2026-04-18

- Reworked the cast result into a more source-like six-yao panel with direct question, cast method, category, time, and shensha rows.
- Corrected the hexagram title and line order so the board reads top-to-bottom like the reference layout.
- Kept the module one-piece and removable while preserving the current tabs and auxiliary sections.

## V1.4.87 - 2026-04-18

- Rebuilt `我该怎么做` into a fuller one-to-one liu-yao layout with 排盘, 日晷, 歌诀, and 六十四卦 sections.
- Expanded the cast runtime with richer盘面 data, including 问念、分类、时间、神煞、互卦、动爻、变卦, and line-level details.
- Upgraded the 六十四卦 catalog into palace-grouped cards with tags and full 64-hexagram coverage.
- Restored the 歌诀 section with built-in long-form mnemonic content and a local add-note flow.
- Kept the module isolated so future deletions can still be done by section without affecting the rest of the app.

## V1.4.86 - 2026-04-18

- Expanded `我该怎么做` toward a more one-to-one liu-yao mapping with dedicated `select-gua`, `reference`, `all-gua`, `calendar`, `clock`, `records`, `songs`, `detail`, and `songs/add` entry points.
- Added a `参考` surface for direction, shengke, wangshuai, and basic imagery so the module matches the source app's auxiliary guidance more closely.
- Added mutual-hexagram output to the cast flow and introduced dedicated detail and song-add pages so the module can be split apart later with less ambiguity.
- Kept the module isolated behind `/persona-api/how-to-do` and the `/how-to-do/*` frontend routes for easy removal.

## V1.4.85 - 2026-04-18

- Re-embedded the `我该怎么做` module as a standalone six-yao toolset again, using the `likeSo/liu-yao` library as the new source reference.
- Restored the top-level entry, landing page, route, backend router, frontend service, and backend runtime so the module can be removed later as one strip-friendly unit.
- Completed the full six-yao surface with cast, hexagram catalog, calendar, clock, records, and songs views under the same project UI system.
- Added regression coverage for the 64-hexagram catalog and the AI-backed cast flow.

## V1.4.84 - 2026-04-18

- Removed the embedded `我该怎么做` feature and its route, returning the app to the no-feature state before that module was introduced.
- Deleted the standalone frontend page, frontend service, backend schema, backend router, backend service, and related tests so the feature can be fully stripped.
- Left the rest of the reply assistant and seed flows untouched.

## V1.4.83 - 2026-04-18

- Added a dedicated six-yao path under `我该怎么做` with separate time-cast and manual-cast inputs.
- Expanded the six-yao result to show the main hexagram, transformed hexagram, changing lines, and line-level guidance.
- Kept Zhouyi and BaZi unchanged while isolating the new six-yao flow so it can be stripped independently if needed.

## V1.4.82 - 2026-04-18

- Added an embedded `我该怎么做` consultation page that maps the Zhouyi AI repo into a single, strip-friendly UI module.
- Wired the page to the project's backend-configured LLM instead of a separate DeepSeek key flow, keeping the model source consistent with the rest of the app.
- Embedded the core `周易64卦 / 六爻 / 八字` result flows with a compact AI interpretation layer and kept the feature isolated in its own route and service.

## V1.4.81 - 2026-04-18

- Aligned reply-corpus admin fields with the reply assistant's object and scene selectors so corpus feeding uses the same vocabulary as the frontend.
- Added text-file import for reply corpora so admin can append local `.txt`, `.md`, `.csv`, or `.log` materials directly into the corpus box.
- Clarified corpus sorting as display priority and kept enabled corpora scoped into the reply assistant runtime only when their object and scene match.

## V1.4.80 - 2026-04-18

- Added a dedicated admin opening for `我该怎么回` reply corpora so users can feed targeted examples like high-EQ replies and workplace refusals.
- Kept the corpus flow separate from LLM config, using it only as prompt grounding for the reply assistant instead of training or long-term memory.
- Added admin CRUD for reply corpora and wired the enabled corpus text into the reply assistant runtime and chat bridge.

## V1.4.79 - 2026-04-18

- Added hidden recent-turn payloads so reply generation can compress the latest chat context without changing the UI.
- Locked the reply assistant's person and scene selectors once a chat starts, with a simple message telling users to start a new conversation instead of switching mid-thread.
- Kept the replay and history behavior unchanged for users while improving backend continuity.

## V1.4.78 - 2026-04-18

- Strengthened reply assistant context by sending recent turns into each generation request.
- Locked target person and scene after a conversation starts, with a simple warning that switching mid-chat can skew the answer.
- Kept the reply assistant history local while making reopened conversations feel more continuous.

## V1.4.77 - 2026-04-18

- Moved the reply page `+`, advanced toggle, file, and image buttons onto one compact row above the send button.
- Reduced the reply page typography to a more restrained chat-style scale.
- Switched the mobile bottom navigation to a four-column flat layout so the labels stay in one row.

## V1.4.76 - 2026-04-18

- Moved the reply page attachment row to sit above the send button for a tighter composer layout.
- Removed mobile image capture forcing so image pickers can use the photo library as well as the camera.
- Updated the top navigation labels to match the current page context across `Seed`, `创建`, `我该怎么回`, and `我该怎么做`.

## V1.4.75 - 2026-04-18

- Renamed the four reply output labels to match the simplified chat flow.
- Added a compact left-corner history drawer with pin, rename, and delete actions.
- Kept reply history local to the page so past conversations can be reopened quickly.

## V1.4.74 - 2026-04-18

- Removed the remaining top-facing labels from `我该怎么回` so the page opens straight into the conversation window.
- Removed the assistant label from the chat flow and kept the screen focused on the actual reply output and composer.

## V1.4.73 - 2026-04-18

- Reworked `我该怎么回` into a chat-window layout with a bottom composer, quick context expansion, file/image attach buttons, and an advanced drawer.
- Kept the answer output in the same four-part structure while moving the interaction into a ChatGPT-like flow.
- Added compact context controls for person type and scene so the page can stay focused on the conversation input.

## V1.4.72 - 2026-04-17

- Reverted the last copy-trimming pass and restored the previous page text density.
- Kept the release history monotonic by recording the rollback as a new version instead of lowering the version number.

## V1.4.70 - 2026-04-17

- Kept the original home page content intact while making the top-level `Seed` entry point back to `/`.
- Pointed the `Seed` dropdown's `Seed` item back to the original home page and kept `创建` pointing to the create flow.
- Preserved the rest of the top navigation layout, including `我该怎么回`, `收藏`, and `个人`.

## V1.4.69 - 2026-04-17

- Replaced the top-level `首页` nav item with a single `Seed` entry.
- Kept `Seed` as a dropdown menu with `创建 / Seed` destinations and removed the separate top-bar `Seed` item.
- Preserved the existing reply assistant and other top-level entries while narrowing the primary seed entry to one consistent menu.

## V1.4.68 - 2026-04-17

- Split `我该怎么回` into a top-level landing page and a deeper reply workbench route.
- Added a homepage-style dual-sticker landing page for `我该怎么回` and `我该怎么做` so the section entrance mirrors the home screen.
- Kept the existing reply assistant functionality intact on a separate workbench route while preserving the same top-level nav experience.

## V1.4.67 - 2026-04-17

- Converted the family-companion fill flow to the same one-page-one-item pattern used by the self-mainline flow.
- Kept the family companion board on a step-by-step page flow with previous/next navigation and a final review card set.
- Preserved the existing skill mapping and field model while changing only the interaction pattern.

## V1.4.66 - 2026-04-17

- Synchronized the fill UI across self-main, source creation, workplace relations, intimate relations, family companionship, and reunion flows.
- Reworked the create wizard into a one-page-one-item flow for every creation board, with previous/next navigation and a final review page.
- Kept the fill experience H5-friendly by removing leftover side-tab style patterns and aligning the card surfaces to the self-main visual system.
- Preserved the existing skill and field logic while changing only the fill-page interaction pattern.

## V1.4.63 - 2026-04-17

- Simplified the self-unified fill page for H5 and mobile use.
- Removed the side rail and compressed the page into a single-column flow that shows the current page content directly.
- Removed the helper-style explanatory copy so the fill assistant stays focused on the current page input itself.

## V1.4.62 - 2026-04-17

- Restored the fill assistant to the model-backed runtime so it can actually read the current page, question type, and form context.
- Added question classification on the backend so the assistant can better distinguish meaning, how-to-fill, missing-material, and depth-related questions.
- Kept a page-specific fallback in place so the assistant still answers the current page even when the model is unavailable.

## V1.4.61 - 2026-04-17

- Further simplified the self-unified creation wizard for small-screen use.
- Trimmed the step rail and repeated helper copy so each screen feels closer to a one-step flow.
- Kept the embedded fill assistant scoped to the current page while making its guidance more compact and page-specific.

## V1.4.59 - 2026-04-17

- Simplified the self-unified creation wizard copy so each page feels lighter and more step-by-step.
- Hardened the embedded fill assistant so refused or invalid model outputs fall back to clear page-specific guidance instead of showing `Not Found`.
- Kept the assistant scoped to the current page while making its answers more concrete about what to fill and what to do when materials are missing.

## V1.4.58 - 2026-04-17

- Reworked the self-unified creation flow into a step-by-step page wizard.
- Added a preparation page, single-page fill navigation, and a final summary page for self creation.
- Kept the existing skill and field logic intact while changing only the interaction pattern.
- Added direct jump-back editing so users can revise any filled item at any time.

## V1.4.57 - 2026-04-17

- Added an embedded "填写助手" inside the self-unified creation flow.
- Kept the helper scoped to self skill explanation and form-filling guidance only.
- Reused the large-model runtime through a dedicated fill-assistant endpoint.
- Added an in-page chat dialog and quick prompts for self-form explanations.

## V1.4.56 - 2026-04-17

- Turned the self-main depth selector into a real upgrade path from light to standard to deep.
- Defaulted new self-main starts to light mode so first-time users can try a smaller input surface before upgrading.
- Tuned the self analysis and follow-up interview runtime so light asks fewer questions, standard keeps the current flow, and deep adds another pass of summary and validation questions.
- Surfaced the current depth path in both the self wizard and the result page while keeping the embedded self-unified skill mapping intact.

## V1.4.55 - 2026-04-17

- Reworked the self-main follow-up section into a structured question picker with a modal answer dialog and add/remove entries.
- Kept the self interview flow compatible with the backend by serializing answers as `问题｜答案` lines.
- Preserved the existing self-unified skill mapping and the optional custom follow-up text field as an embedded upgrade, not a replacement.

## V1.4.54 - 2026-04-17

- Upgraded the self-main creation flow into an embedded source-driven distillation chain with a structured analysis report and follow-up interview stage.
- Added a reusable persona analysis report that summarizes identity, beliefs, expression style, work style, timeline, external feedback, and missing dimensions.
- Added dynamic follow-up questions that are derived from the analysis report and can be answered to fill the gaps before final distillation.
- Kept the existing self-unified layers and legacy compatibility fields intact so old self skills and saved objects still round-trip safely.
- Surfaced the new five-step workflow in the self creation page and result page without replacing the original skill mapping layer.

## V1.4.53 - 2026-04-17

- Upgraded the self-main creation flow from a form-style profile into a source-driven self-distillation workflow.
- Split self personas into identity, decision-rules, voice, and knowledge-sources layers.
- Added question-type routing so self personas answer differently across career, learning, product, decision, and reflection scenarios.
- Introduced dynamic knowledge-source support for time-sensitive self questions.
- Added boundary rules and validation cases so the self line reflects how the person actually judges, not just how they talk.

## V1.4.52 - 2026-04-17

- Rebuilt `我该怎么回` around a strict answer-first output protocol.
- Ensured the reply assistant actually calls the model after skill-side preprocessing.
- Kept skills as internal filters and constraints instead of exposing their intermediate reasoning to users.
- Collapsed advanced materials into an optional section instead of defaulting to a create-like form.
- Changed the default response shape to one short judgment, one directly sendable reply, one risk note, and one likely consequence.

## V1.4.51 - 2026-04-17

- Added a direct-use top-level feature: 我该怎么回.
- Built a unified reply-assistant runtime instead of a create-first persona flow.
- Integrated crush-skill, relationship-training-skill, xinyi, partner-skill, ex-skill, colleague-skill, teammate-skill, and Atlas-style tone enhancement.
- Added broad reply coverage across intimacy, work communication, family, friends, and formal scenarios.
- Reused the shared file/image/OCR material layer for reply understanding and style grounding.

## V1.4.50 - 2026-04-17

- Merged the intimate understanding and maintenance paths into one visible relationship-management entry and absorbed crush-skill as the message-push / send-preview layer.
- Normalized legacy relationship-management aliases so the create wizard no longer renders duplicate relationship-management cards.
- Preserved understanding, maintenance, balanced, and message-push runtime weights while keeping the existing intimate chat flow intact.
- Surfaced message-push weights and cues in Create result and My Seeds views.

## V1.4.49a - 2026-04-17

- Removed the duplicated relationship-management choices from the create-wizard selection step.
- Normalized legacy relationship-understanding and relationship-maintenance keys into one canonical relationship management entry.
- Kept the underlying understanding, maintenance, and message-push runtime behavior intact while cleaning up the visible selection surface.

## V1.4.49 - 2026-04-17

- Merged the relationship understanding and relationship maintenance paths into a single relationship management entry.
- Kept understanding-side and maintenance-side skills under one runtime with dynamic weighting from uploaded materials.
- Unified relationship memory, interaction samples, style samples, and reply cues under the relationship management object model.
- Surfaced relationship management focus and weights in Create result and My Seeds views.

## V1.4.48 - 2026-04-17

- Calibrated reunion chat into light, medium, and deep progressive recall stages so memory comes back more gradually.
- Tightened reunion safety guardrails to keep certainty claims, dependency reinforcement, and supernatural wording out of replies.
- Tuned reunion layered-memory retrieval so procedural, episodic, and semantic memories are recalled in a more context-aware order.
- Kept OCR, guided recollection, and shared upload materials in the reunion creation chain while making their chat-facing behavior more restrained.
- Surfaced recall stage and guardrail summaries more clearly in reunion result and My Seeds views.

## V1.4.47 - 2026-04-17

- Upgraded the reunion persona path with progressive recall, layered memory, and safety guardrails.
- Added guided recollection prompts for reunion creation so low-material paths can still build a richer memory base.
- Adjusted reunion summary generation so guided recollection remains visible in saved Seeds instead of being truncated away.
- Kept reunion as its own branch while routing OCR and shared upload materials into the reunion distillation chain.

## V1.4.46 - 2026-04-17

- Added a shared material capability layer across all creation flows.
- Unified text file upload, image upload, and OCR extraction for family, reunion, intimate, and self creation.
- Routed OCR-extracted text into each path's distillation pipeline and preserved it in raw materials.
- Surfaced file, image, and OCR summaries consistently in Create result and My Seeds.
- Ensured future creation flows inherit upload and OCR support by default.

## V1.4.45 - 2026-04-17

- Added OCR-based text extraction for family companion image materials.
- Let uploaded family screenshots and photos flow through OCR into raw materials, family memory distillation, and chat recall.
- Kept image notes as a fallback while preserving uploaded images as material assets and surfacing OCR summaries in result and My Seeds views.
- Preserved the existing family companion and family subtype flows without adding new persona entry points.

## V1.4.44 - 2026-04-17

- Added mobile-friendly family companion photo upload support in the create wizard.
- Kept text uploads intact while allowing image files to be selected from album or camera on mobile.
- Preserved image notes as the primary distilled source and carried uploaded image metadata through raw materials, result summaries, and My Seeds.
- Added regression coverage for family image materials without changing the existing family companion business flow.

## V1.4.43 - 2026-04-17

- Extended family memory from a flat summary into layered episodic, semantic, and procedural memories.
- Added optional guided memory collection to family companion creation and preserved it through draft, save, and summary surfaces.
- Adjusted family summary generation so guided recollection is visible in My Seeds instead of being truncated away.
- Upgraded family companion retrieval to rank memories by emotion, topic, subtype, and memory layer.

## V1.4.42 - 2026-04-16

- Unified the family-companion entry around a single visible `家人陪伴` path while preserving the `妈妈 / 父母 / 其他家人` subtype split internally.
- Weighted the family draft and reply flow so `mother` leans more on MamaSkill-style emotional support and `parents` leans more on parents-skills-style shared memory and stable advice.
- Kept `reunion-skill` separate as its own `重逢人格` branch and persisted `family_subtype` through create, result, My Seeds, and chat surfaces.
- Added regression coverage for `mother`, `parents`, and `other_family` family draft and chat-context differences.

## V1.4.41 - 2026-04-16

- Upgraded the H5 frontend for mobile browsing and touch interaction.
- Improved spacing, card rhythm, button sizing, form readability, and night-mode contrast across the main pages.
- Kept all APIs, routes, fields, business logic, and skill flows unchanged.

## V1.4.40 - 2026-04-16

- Reverted the Me page from stacked cards back to a flat three-card layout.
- Kept the hover feedback but removed the overlap and lift behavior that made the personal-center entries feel inconsistent.
- Preserved the same three entries while simplifying the interaction model.

## V1.4.39 - 2026-04-16

- Strengthened the Favorites card lift and click response so all three Me page cards now feel interactive.
- Added a quick pop animation and stronger hover/press shadow for the personal-center stack.
- Kept the semi-overlapped structure while making the middle card's motion easier to perceive.

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

## V1.4.65
- Removed `我该怎么回` from the create entry flow so it stays a standalone top-level feature
- Removed the reply-assistant branch from the create wizard and aligned the fill pages more closely with the self-mainline visual system
- Unified fill-page surfaces and form cards around the same warm H5-friendly card language
- Fixed the `Seed` and `我该怎么回` hover dropdown gap so submenu items stay reachable

## V1.4.64
- Reworked the top navigation into hover dropdowns for `我该怎么回` and `Seed`
- Added a placeholder `我该怎么做` page for the future flow
- Removed the reply-assistant sticker from the homepage and centered the remaining creation/seed tiles
- Tightened night-mode label and menu contrast so nav options stay readable

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
