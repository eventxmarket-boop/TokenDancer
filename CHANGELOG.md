## V1.4.317
- Added the same writable alert-file fallback to the Google Form watcher so the short-link probe can no longer crash on the server when its configured alert path points at a local macOS directory.
- Bumped the form-page state version so the watcher reseeds after this deployment instead of carrying a stale baseline through the new write-path behavior.

## V1.4.316
- Stopped the Mescladís public-page watcher from persisting probe failures into its baseline, so a timeout or browser abort no longer turns into a fake page-update alert on the next successful poll.
- Kept the alert-file fallback from the previous fix, but now the watcher only advances state on successful page snapshots and ignores transient fetch errors instead of comparing them as content changes.

## V1.4.315
- Added a writable alert-file fallback to the Mescladís public-page watcher so a server deployment can no longer crash just because the configured alert path points at a local macOS directory.
- Kept the canonical page hashing logic unchanged, but now the watcher writes alerts to the configured path when possible and falls back to a repo-local file instead of exiting on ENOENT.

## V1.4.314
- Downgraded the Google Forms short-link watcher to an alias/redirect check so it no longer emits page-updated alerts every poll when the short URL resolves to the stable docs.google.com form page.
- Kept the final Google Form page watcher active as the content-change source, so real form content changes still notify while the short-link watcher now only records alias drift.

## V1.4.313
- Stopped the Google Form watcher from hashing the resolved URL along with the visible content, so short-link redirect noise no longer shows up as a fresh page update every poll.
- Added a form-page state version marker so old hashes are reseeded after this normalization change instead of triggering one more false alert on deploy.

## V1.4.312
- Broadened the Mescladís main-monitor burst suppression so a shared error wave across multiple targets is treated as one global incident instead of leaking separate ERROR alerts for each target signature.
- Kept the per-target confirmation and cooldown logic in place, but now any target-level ERROR inside an active burst incident is suppressed regardless of whether the individual error string is identical to the first one.

## V1.4.311
- Added a per-target error notification cooldown to the main Mescladís monitor so a flapping target can no longer re-alert immediately after a brief recovery and re-failure cycle.
- Kept the existing consecutive-failure confirmation threshold, but now the monitor remembers the last error notification window in state and suppresses repeated Telegram alerts until the cooldown expires.

## V1.4.310
- Added a dedicated Mescladís blog watcher for `https://mescladis.org/blog/` so the blog content can be monitored independently from the announcement page and homepage button watchers.
- Gave the blog watcher its own environment keys, alert file, state file, service template, and package script so it can baseline the visible blog text and notify when that text changes without sharing state with the rest of the Mescladís links.

## V1.4.309
- Added a dedicated Mescladís home-page button watcher for `https://mescladis.org/` so the visible `Nuevas citas` control can be tracked independently from the announcement-page watcher.
- Gave that button watcher its own environment keys, state file, alert file, and systemd service template so it can baseline the root page and alert when the button text or destination changes without sharing state with the other public-page monitors.

## V1.4.308
- Switched the Mescladís public-page monitor example configuration to the canonical `https://mescladis.org/nueva-cita-previa-regularizacion/` URL so future deployments do not keep pointing at the legacy alias.
- Kept the public-page cleanup and state-versioning logic in place, so the watcher still normalizes the page snapshot and reseeds cleanly after any URL/shape change.

## V1.4.307
- Added four more Mescladís monitoring targets (8 through 11) to the main appointment monitor so the new links are included in the same probe-and-alert pipeline as the existing seven targets.
- Updated both the runtime `.env` and `.env.example` target lists so the new URLs are available to local runs and future deployments without changing the monitor code again.

## V1.4.306
- Added a public-page state schema version so the Mescladís announcement monitor will reseed its baseline after a snapshot-format change instead of treating the upgraded hash as a real content update.
- Kept the main/article cleanup from the previous version, but now old `public_page_state.json` entries are treated as stale and replaced on the next run, preventing another false "page updated" alert after deploy.

## V1.4.305
- Narrowed the public-page monitor to hash a cleaned main/article content snapshot instead of the full body text, so the Mescladís announcement page no longer trips on cookie banners, nav chrome, or footer noise.
- Kept the canonical URL normalization in place, but now the comparison ignores the common cookie dialog and site shell fragments that were causing false "page updated" notifications even when the announcement content stayed the same.

## V1.4.304
- Normalized repeated transient probe failures into a small set of shared signatures such as network disconnect, socket disconnect, fetch failure, timeout, and interrupted navigation, so a single brief outage is no longer amplified into dozens of separate ERROR events across lanes and targets.
- Kept the existing error-confirmation threshold and state locks, but made burst suppression actually work across the Mescladís targets by collapsing per-URL noise into shared incident categories.

## V1.4.303
- Added a direct visible-element slot click path so the Montjuic / Z-chain executor no longer depends only on text-locator matching when the rendered booking button is present but nested or shaped differently in the DOM.
- Kept the exact-slot and nearby-hour candidate search in place, but made the final click path scan visible clickable elements by normalized text and aria/title content before falling back to the older locator-based search.

## V1.4.302
- Extended the nearby-hour slot fallback to include compact button-label variants like `1:30pm` and `1:30PM`, not just spaced forms, so the executor can match the actual Google Calendar slot buttons rendered without a space.
- Kept the exact-slot search first and the nearby-hour fallback second, so the executor still prefers the bridge-provided time before trying adjacent-hour rescue matches.

## V1.4.301
- Added a nearby-hour fallback to the slot matcher so the executor can still match the rendered button when the bridge payload and the visible booking page differ by one hour, which was causing repeated `slot miss` failures on Mescladís pages.
- Kept the exact slot search and the post-date-click wait intact, so the executor now tries the precise slot first and only falls back to adjacent-hour variants if the exact match is missing.

## V1.4.300
- Fixed the Montjuic / Z-chain slot candidate builder so the broader date-and-time labels now construct their month strings before using them, preventing the executor from crashing while generating exact slot matches.
- Kept the widened slot candidate set and short post-date polling window, so the executor can now use the richer labels instead of failing on undefined month variables.

## V1.4.299
- Fixed a slot-candidate regression in the Montjuic / Z-chain executor where the expanded date-and-time button labels referenced `monthDay` before it was defined, which caused the execution path to crash while trying to match the rendered slot control.
- Kept the widened slot matcher and post-date-click wait in place so the executor can now actually use the broader candidate set instead of failing on the first generated label.

## V1.4.298
- Broadened the slot matcher for Montjuic and the Z-chain executor so it can recognize the full appointment button labels that include both the date and time, instead of only searching for the bare time text and missing rendered slot controls.
- Added a short post-date-click polling window so the executor waits for the slot controls to appear before attempting the exact slot click, reducing false `slot miss` failures on pages that render the time buttons a moment later.

## V1.4.297
- Added Chinese submit-button matching so the Z-chain executor can recognize bottom-right controls labeled `取消 / 预定`, `预定`, and `预订` instead of missing the final submit action on localized booking pages.
- Kept the redirected booking-page guard and commit-navigation path intact so the executor still stays on the already-open page before filling.

## V1.4.296
- Stopped the Z-chain executor from reloading an already redirected Google booking page just because the current URL no longer matches the short-link target, which was wasting the manual fill window on Mescladís 1 and other appointment pages.
- Kept the `commit` navigation cap and booking-page URL guard in place so the executor can stay on an already-open booking page and go straight into date/slot selection instead of restarting the page load path.

## V1.4.295
- Switched the Mescladís/Z-chain page navigation step to `waitUntil: 'commit'` with a shorter cap so the bridge and executor stop burning the full DOMContentLoaded timeout before they can reach schedule lookup.
- Kept the signal-driven execution path intact, but made the first navigation step fail much faster on slow Google appointment pages.

## V1.4.294
- Added an installer that can generate independent Mescladís z-chain systemd instances from target 1 through 7 so each target gets its own bridge, executor, env file, state, heartbeat, and signal path.
- Added a package script for installing the per-target z-chain instances in one shot.
- Kept the existing Mescladís 4 and test chains intact while filling the missing per-target deployment slots.

## V1.4.293
- Removed the execution-side timezone guess from the Z-chain autofill path so the executor always uses the configured slot timezone instead of reinterpreting the page text.
- Replaced the broad slot fallback search with a strict signal-slot click path that only tries candidates derived from the bridge payload, so the executor stops wandering through generic slot hunting.
- Kept the bridge/executor split intact while making the execution side fail fast if the signal slot is not actually rendered.

## V1.4.289
- Hardened the Z-chain error state so a single probe failure is treated as transient and only a second consecutive failure is emitted as `ERROR`, with the bridge tracking an `errorCount` in snapshot state to avoid flooding Telegram on short-lived navigation/network blips.
- Added month-alignment before the Z-chain date click path so the executor now pages forward or backward to the slot's month before selecting the day, instead of misfiring on the currently visible calendar month and missing the slot.
- Expanded the post-submit confirmation detector to recognize the booking success copy that includes `已确认预订`, `邮件已发送至`, and `请取消预约`, so the executor can treat the final confirmation page as success instead of leaving the booking result ambiguous.
- Removed the post-submit confirmation wait from the Z-chain autofill path so the executor now treats the submit click as the terminal action instead of spending extra time trying to infer a confirmation page.
- Broadened the submit-button matcher to include the common submit labels and added a force-click fallback so the executor can get through a plain submit step without waiting on a second click or confirmation text.

## V1.4.288
- Tightened the Z-chain date/time click path so it now prefers visible button/link matches and falls back to force-clicking the first visible appointment-time control instead of missing an already-rendered slot.
- Applied the same visible-match helper to the booking-date click path so date selection and slot selection use the same stricter click logic.

## V1.4.287
- Added a time-button fallback to the Z-chain executor so, after exact slot text matching fails, it can still click the first visible appointment-time control instead of stopping at slot miss.
- Kept the timezone conversion and retry-safe consumption reset, but gave the executor a second path for pages that render the correct day while changing the displayed time text.

## V1.4.286
- Made the Z-chain slot matcher timezone-aware so the executor converts the signal slots from the source slot timezone into the booking page's displayed timezone before it looks for clickable time buttons.
- Kept the retry-safe consumed-signal reset from the previous patch, so a slot miss can be re-queued instead of being burned as already processed.

## V1.4.285
- Changed the Z-chain consumer so a failed slot-click attempt no longer burns the same OPEN snapshot as consumed.
- If the executor hits a slot miss, it now clears the autofill signature and can re-queue the same open snapshot instead of silently skipping retries.
- Kept the date-first click path and timezone detection in place while making the execution path retry-safe for a live open slot.

## V1.4.284
- Added page-timezone detection to the Montjuic/Z-chain autofill so the executor now converts the signal slots into the timezone actually rendered by the booking page before matching buttons.
- Kept the slot-timezone browser context, but now the click path can follow a Singapore-rendered page when the site exposes `GMT+08:00` in the visible text instead of failing the slot lookup against Madrid-formatted candidates.

## V1.4.283
- Fixed the Z-chain test executor browser-context call so it now awaits the Playwright context before creating the page, which removed the `getBrowserContext(...).newPage is not a function` crash.
- Kept the slot-timezone browser context so the executor still renders in the same timezone as the slot candidates after the crash fix.

## V1.4.282
- Forced the Montjuic/Z-chain browser context to use the slot timezone so the executor now renders the appointment page in the same timezone as the slot candidates instead of the server default.
- Kept the date-first execution path, but removed the timezone mismatch that was causing the executor to see a clickable day while failing to match the corresponding time slot.

## V1.4.281
- Routed the Mescladís Test executor onto the dedicated test env file as well so both test bridge and test executor stop inheriting the shared repo .env identity.
- Kept the main Mescladís 4 chain on its own service path while fully isolating the test executor from the 4-chain runtime.

## V1.4.280
- Split the Mescladís Test Z-chain service onto its own dedicated environment file so systemd no longer inherits the shared repo .env values that were forcing the test runtime back onto Mescladís 4.
- Kept the independent bridge/executor split intact while making the test unit source only the test-specific chain identity and CSV queue.

## V1.4.279
- Quoted the Z-chain systemd environment values so Mescladís Test can carry its full target name and URL through systemd without space-splitting the env assignment.
- Kept the dedicated Mescladís Test bridge/executor units and CSV queue split intact while fixing the service-layer env parsing that was still leaking the 4-chain identity into the test runtime.

## V1.4.278
- Fixed the Z-chain wrapper executable bit so the bridge service can actually start under systemd on Ubuntu instead of failing with 203/EXEC.
- Kept the dedicated Mescladís Test service split in place, with its own CSV queue and its own systemd units.

## V1.4.277
- Added dedicated Z-chain systemd units and a dedicated CSV queue for Mescladís Test so the test target now has a fully independent bridge and executor pair instead of sharing the Mescladís 4 service path or its profile queue.
- Kept the existing wrapper-based Z-chain architecture intact while making both the main chain and the test chain explicit in their own service definitions and profile sources.

## V1.4.276 - 2026-04-29

- Replaced the hardcoded `/Users/chanzi/.qclaw/...` runtime defaults in the Z-chain wrappers and executor bootstrap with `$HOME/.qclaw/...` so the same bridge/executor architecture can run on Ubuntu servers without ENOENT failures.
- Kept the instance-scoped bridge/executor file separation, but now each chain derives its alert, state, and heartbeat paths from the current machine's home directory instead of a Mac-only path.
- Preserved the date-first click path and prewarmed execution page so the faster fill flow remains intact after the runtime-path fix.

## V1.4.275 - 2026-04-29

- Aligned the Z-chain launch entrypoints with the wrapper-based architecture so the monitor service now starts through `deploy/run_z_chain.sh` instead of bypassing the instance-scoped bootstrap path.
- Switched the npm `zchain:monitor` and `zchain:executor` scripts to the wrapper launchers so local runs and service runs follow the same isolated bridge/executor setup.
- Kept the independent bridge/executor file namespaces intact so per-target chains continue to derive their own alert, state, and heartbeat files from `Z_CHAIN_INSTANCE_ID`.

## V1.4.274 - 2026-04-29

- Added instance-scoped defaults to the Z-chain wrappers so independent monitor/executor pairs can derive their own alert, state, and heartbeat files from `Z_CHAIN_INSTANCE_ID` instead of colliding on one shared runtime path.
- Prewarmed the isolated Montjuic/Z-chain executor page so the consumer keeps a live browser page on the target URL and reuses it when a signal arrives instead of cold-starting a new page for every slot attempt.
- Added a date-first click pass ahead of slot clicking so the executor can open the correct calendar day from the signal before it searches for the time slot text.

## V1.4.273 - 2026-04-29

- Added a date-first click pass to the isolated Z-chain autofill so the executor now tries the calendar day from the signal before searching for the time slot text.
- Kept the direct slot click path as the first attempt, but now the executor can open the right day first when the page hides times until a date is selected.
- Logged whether the date click landed, so we can separate a missing date step from a missing time step on the next live run.

## V1.4.272 - 2026-04-29

- Split the Z-chain runtime files so the bridge and executor no longer share the same state or heartbeat paths.
- Routed the bridge through `z_chain_monitor.js` as a signal emitter and the new executor through `z_chain_executor.js` as the only autofill consumer.
- Kept the shared alert file as the handoff, but made the bridge and executor use distinct state and heartbeat files so they cannot overwrite each other.

## V1.4.271 - 2026-04-29

- Split the Z-chain into a bridge and a dedicated executor so the monitor can emit open-slot signals without also trying to fill the form in the same process.
- Added a consumer mode that watches the shared alert file, consumes only fresh OPEN signals, and runs the autofill/submission flow independently from the probe loop.
- Disabled Telegram noise on the bridge side so the signal file becomes the handoff point and the executor owns the booking attempt.

## V1.4.270 - 2026-04-29

- Forced the Z-chain wrapper onto a single lane starting at offset `0` so the autofill worker stops competing with the multi-lane production monitor and reacts to an open slot as fast as possible.
- Set the Z-chain lane interval to the chain poll interval, with a fast fallback, so the dedicated worker can keep rechecking without waiting for the shared 0/10/20 lane schedule.

## V1.4.269 - 2026-04-29

- Added a dedicated birth-date rescue pass to the Montjuic/Z-chain autofill so the booking flow no longer stalls when the eighth field is rendered differently from the other contact fields.
- Kept the earlier modal settle and ordered fallback, but now the date field gets its own label, placeholder, and last-visible-input search before the chain gives up.

## V1.4.268 - 2026-04-29

- Added a short post-modal settle before the Montjuic/Z-chain autofill starts so the contact sheet has time to finish rendering before the field pass runs.
- Lowered the positional fallback threshold so the ordered input pass can still fill the eight contact fields when the modal exposes only a small subset of labels up front.

## V1.4.267 - 2026-04-29

- Made the Montjuic/Z-chain autofill reload its profile queue before each autofill run so a newly provided profile can be consumed immediately without waiting for a restart.
- Replaced the queue head with the new `Fuentes / Hina` profile so the next open slot uses the new data instead of the prior placeholder entry.

## V1.4.266 - 2026-04-29

- Made the Montjuic/Z-chain autofill cursor advance through the profile queue so each open slot can consume the next profile automatically instead of requiring manual profile selection.
- Kept the exact-field, auto-submit, and confirmation-only behavior intact so the flow still runs end-to-end once a slot is available.

## V1.4.265 - 2026-04-29

- Suppressed the normal Montjuic/Z-chain status alerts while the auto-submit flow is running, so the chain only pushes the final confirmation signal instead of emitting repeated OPEN/FULL churn for the same slot.
- Kept the confirmation alert path enabled, which means the booking result can still be reported without flooding Telegram with the same slot's intermediate status flips.

## V1.4.264 - 2026-04-29

- Excluded the hidden reCAPTCHA textarea from the positional Montjuic/Z-chain autofill fallback so the final birth-date field is no longer shifted onto the captcha element.
- Kept the label-based matching and the ordered fallback together, which should now fill the eight visible fields in the expected Google Bookings order.

## V1.4.263 - 2026-04-29

- Added a positional fallback for the Montjuic/Z-chain autofill flow so the page can still be filled when the Google Bookings labels are not bound to their inputs in a way Playwright can resolve.
- Extended the text matchers for the first-name, last-name, phone, email, and address fields so both the English Google Bookings labels and the Spanish labels are handled in the same chain.

## V1.4.262 - 2026-04-29

- Added the missing `settleAfterAction` helper back into the Montjuic/Z-chain autofill path so the post-click waits used by the slot-to-form flow no longer crash the chain.
- Kept the absolute-path fix and the longer post-navigation slot render wait from the previous patch.

## V1.4.261 - 2026-04-29

- Fixed the Montjuic/Z-chain state and heartbeat path resolution so absolute paths like `/tmp/...` are no longer rewritten under the repository root, which had been breaking autofill state writes.
- Increased the post-navigation wait before slot clicking so the live Google Bookings modal has time to render the `3:20pm`/`3:30pm` slot before the autofill chain tries to click it.

## V1.4.260 - 2026-04-29

- Stopped normalizing the Montjuic/Z-chain birth date before fill so the form receives the user-provided date format exactly as entered, which matches the working `29/10/1988` path on this booking page.
- Added the Google Bookings `Book` button to the submit matcher so the autofill chain can actually trigger the final booking step instead of stopping at the modal.

## V1.4.259 - 2026-04-29

- Expanded the Montjuic/Z-chain slot click matching so compact time labels like `3:30pm` are now recognized alongside the spaced variants.
- Kept the exact-field autofill path in place and only widened the slot-candidate generation, which should help the auto-fill step actually enter the open slot before populating the eight labels.

## V1.4.258 - 2026-04-29

- Tightened the Montjuic/Z-chain field matcher to the exact eight user-provided labels, including the full Spanish address label and the document-number label variants, so the autofill path is less likely to spill into nearby fields.
- Kept the isolated Z chain behavior intact while making the form-root discovery prefer the exact label set the user provided.

## V1.4.257 - 2026-04-29

- Added a separate autofill trigger mode for the isolated Z chain so it can fill once for each new open-slot snapshot instead of relying only on a status transition from the existing snapshot state.
- Kept the Montjuic default behavior intact for the existing chain while wiring the Z chain to the new `any_open_snapshot` mode by default, which avoids missing the first usable slot after a release.

## V1.4.256 - 2026-04-29

- Added an isolated `z_chain_monitor.js` wrapper so the booking-fill workflow can run under its own `Z_CHAIN_*` environment without colliding with the existing Montjuic or appointment watchers.
- Extended the Montjuic autofill path to capture confirmation-page text after submission when confirmation capture is enabled, while keeping that behavior off by default for the existing chain.
- Added a separate `zchain:monitor` entrypoint, `z_chain_profiles_template.csv`, and matching `Z_CHAIN_*` example configuration so the new chain can be deployed independently and tested later with a real profile set.

## V1.4.255 - 2026-04-28

- Stopped the main Mescladís monitor from promoting confirmed probe failures into the durable snapshot, so a transient ERROR no longer reappears later as a noisy ERROR -> FULL recovery alert.
- Kept the existing consecutive-failure confirmation for real errors, but only preserve the separate error incident record instead of overwriting the stable appointment snapshot.

## V1.4.254 - 2026-04-28

- Added a 30-second in-loop heartbeat pulse and unique temp-file writes so the main monitor no longer loses heartbeat updates when concurrent lanes collide on the same temp path.
- Switched each target probe to its own short-lived browser page so one lane can no longer accidentally reuse another lane's page context and trigger spurious navigation and heartbeat stalls.
- Made the health daemon require two consecutive corrupt heartbeat reads before alerting, which filters single transient parse failures without hiding a real monitor hang.

## V1.4.253 - 2026-04-28

- Deferred Mescladís error alerts until the same target fails multiple consecutive probes, so brief navigation or network glitches no longer fire immediate ERROR notifications.
- Kept confirmed errors visible after repeated failures while preserving the existing OPEN and FULL transition behavior.

## V1.4.252 - 2026-04-28

- Normalized the public-page watcher target URL before probing so tracking parameters like `fbclid` no longer create false page-change alerts.
- Added the resolved canonical URL to the public-page event payload so updates are reported against the stable page address instead of the transient tracked link.

## V1.4.251 - 2026-04-28

- Reduced the health daemon default polling interval to 60 seconds so fresh deployments now check the monitor heartbeat once per minute instead of falling back to the older 10-minute default.
- Kept the stale threshold and startup grace unchanged so the health watcher still avoids noisy startup alerts while remaining responsive on long-running hangs.

## V1.4.250 - 2026-04-28

- Added a per-target state lock in the main Mescladís monitor so the three staggered lanes can no longer race each other while comparing, updating, and sending the same target snapshot.
- Made the notification handoff wait for the Qclaw, Telegram, and alert-file branches to settle together, which reduces the chance of a slots reduction being overwritten by a later lane before it is delivered.

## V1.4.249 - 2026-04-28

- Restored the Telegram direct-push credentials in the main monitor environment so Mescladís slot-change alerts can reach Telegram again.
- Kept the staggered Mescladís lane scheduler and RPC snapshot flow unchanged; only the notification credentials were restored.

## V1.4.248 - 2026-04-27

- Added a seventh Mescladís appointment target so the main monitor now covers the newly provided Google Calendar schedule link alongside the existing six targets.
- Kept the staggered lane scheduling and RPC snapshot flow unchanged so the new target inherits the same polling and alert behavior as the rest of the Mescladís set.

## V1.4.247 - 2026-04-27

- Separated transient Mescladís probe failures from the stable state snapshot so an error no longer overwrites the last known good status and later recovery scans are not misreported as page changes.
- Kept the lane scheduler and RPC snapshot flow intact while deduplicating repeated error alerts until a real non-error snapshot arrives again.

## V1.4.246 - 2026-04-27

- Reworked the Microsoft Bookings watcher to validate availability by clicking candidate dates and checking the resulting availability text or visible time-slot grid, which suppresses month-switch jitter and page-text false positives.
- Kept the multi-month scan and stability gate in place so the watcher still requires a repeated match before promoting a changed date set into a real alert.

## V1.4.245 - 2026-04-27

- Added a stability gate to the Microsoft Bookings watcher so a date-list change must repeat before it is promoted from pending to a real notification, which suppresses one-off month flip and layout jitter false positives.
- Kept the month-flipping scan and date-diff-only behavior intact while making the Bookings monitor wait for two matching reads before alerting on an increase or decrease.

## V1.4.244 - 2026-04-27

- Reused the staggered lane scheduler across the remaining page watchers so the public page, Google Forms, Microsoft Bookings, AgendaPro, and Montjuic monitors now follow the same multi-lane polling cadence as the main Mescladís monitor.
- Kept the health daemon separate while preserving each watcher’s own diff rules, so only the scan cadence changed and the alert criteria stayed specific to each page type.

## V1.4.243 - 2026-04-27

- Extended the Microsoft Bookings watcher to keep flipping months while collecting dates, so the monitor can continue across April, May, and June instead of stopping on the default month view.
- Kept the date-diff-only notification rule in place so the watcher still ignores copy/layout noise and only alerts when the extracted booking-date set actually changes.

## V1.4.242 - 2026-04-27

- Narrowed the Microsoft Bookings watcher so it only sends notifications when the extracted booking-date set changes, which suppresses noisy page-copy updates while keeping earlier/later availability changes visible.
- Kept the standalone Microsoft Bookings service isolated from the other monitors and preserved direct Telegram delivery plus the optional alert-file handoff.

## V1.4.241 - 2026-04-27

- Added a standalone Microsoft Bookings watcher for the provided bookings.cloud.microsoft page, with content snapshots, accessible iframe text capture, and extracted booking-date candidates so earlier availability can trigger a notification.
- Added a `microsoftbookings:monitor` entrypoint plus matching `MICROSOFT_BOOKINGS_*` environment variables so the new watcher stays isolated from the existing Google Calendar, AgendaPro, Montjuic, public-page, and form-page monitors while still supporting direct Telegram delivery and an optional alert-file handoff.

## V1.4.240 - 2026-04-27

- Extended the Google Forms watcher to track both the short public form URL and the resolved closed-form page as separate targets, so changes on either URL can trigger their own update notifications.
- Added optional multi-target configuration via `FORM_PAGE_TARGET_URL_ALT` and `FORM_PAGE_TARGETS_JSON` while keeping direct Telegram delivery and the optional alert-file handoff isolated from the existing monitors.

## V1.4.239 - 2026-04-27

- Added a standalone form-page watcher for the provided Google Forms closed page so the repository can baseline the page title and visible text, then notify whenever the content changes.
- Added a `formpage:monitor` entrypoint plus matching `FORM_PAGE_*` environment variables so the new watcher stays isolated from the existing Google Calendar, AgendaPro, Montjuic, and public-page monitors while still supporting direct Telegram delivery and an optional alert-file handoff.

## V1.4.238 - 2026-04-27

- Serialized the Mescladís target probes so concurrent lanes no longer race the same Google Calendar appointment page and trigger spurious `page.goto` / `page.evaluate` interruptions.
- Kept the three-lane staggered cadence and direct Telegram delivery intact while reducing the overnight error bursts caused by lane overlap on shared target pages.

## V1.4.237 - 2026-04-27

- Added direct Telegram Bot API delivery to the AgendaPro, Montjuic, public-page, and health monitor flows so the server can notify without depending on the local qclaw file handoff.
- Kept the existing file-based and webhook-based paths available for local setups while documenting the shared `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` server configuration path.

## V1.4.236 - 2026-04-27

- Added direct Telegram Bot API notification support to the main Mescladís monitor so a server deployment can post alerts without depending on the local qclaw file handoff.
- Documented the new `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` server configuration path while keeping the existing qclaw webhook and alert-file flow available for local setups.

## V1.4.235 - 2026-04-27

- Switched the Mescladís lane scheduler from target sharding to full-set replication so all three staggered lanes scan the complete appointment target list while starting at different offsets.
- Kept the 0s / 10s / 20s lane offsets and updated the docs and env templates so the monitor now behaves as a dense, overlapping multi-lane poller instead of splitting the targets across lanes.

## V1.4.234 - 2026-04-27

- Reworked the Mescladís appointment monitor into three staggered polling lanes with 30-second lane intervals and 0s / 10s / 30s startup offsets so the watcher keeps higher scan density without waiting for one long monolithic round to finish.
- Updated the runtime `.env`, `.env.example`, and README to reflect the new lane-based poll schedule while preserving the existing single-event dedupe behavior.

## V1.4.233 - 2026-04-27

- Switched the Mescladís Google monitor from relative post-round sleeping to wall-clock aligned polling so the next scan snaps to the configured interval grid instead of drifting after each run.
- Kept the single-round, non-overlapping execution model in place while exposing the actual next aligned tick in the runtime logs for easier delay diagnosis.

## V1.4.232 - 2026-04-27

- Reduced the Mescladís Google monitor polling interval to 15 seconds across both the normal and peak windows so the appointment watcher can detect changes faster under the current operating setup.
- Synchronized the runtime `.env` and `.env.example` polling values so the local and sample configurations no longer drift.

## V1.4.231 - 2026-04-25

- Restored the missing bridge-status export wiring for the admin panel so the qclaw test template can consume `/persona-api/image-lab/bridge/status/` without breaking the frontend build.
- Kept the new read-only qclaw probe and slash-aliased status route in place so testers can read bridge state without touching repository code.

## V1.4.230 - 2026-04-25

- Added a read-only qclaw bridge-status probe so external automation can consume `/persona-api/image-lab/bridge/status` without modifying repository code or generated assets.
- Exposed the probe through a package script and admin panel copy so testers have a concrete command path for status-only validation.
- Documented the qclaw test-only flow in the README while keeping the Plus bridge and OpenAI image path unchanged.

## V1.4.229 - 2026-04-24

- Added a standalone public-page watcher for `https://mescladis.org/cita-previa-regularizacion-extraordinaria/` so the repository can baseline the announcement page and emit a notification whenever its visible content changes.
- Added `publicpage:monitor` and `publicpage:daemon` package scripts plus matching `.env` keys so the new watcher can write to its own alert file without affecting the existing appointment monitors.
- Documented the new public-page workflow in the README while leaving the Google Calendar, AgendaPro, Montjuic, and health-monitoring paths unchanged.

## V1.4.228 - 2026-04-24

- Added a sixth Mescladís Google Calendar appointment target so the monitor can watch the newly provided `YQ9pon1Ji49RQQNR8` link alongside the existing test page and five production pages.
- Relaxed the Google monitor target validation from an exact six-entry check to a minimum-six-entry check so the added Mescladís target does not break the existing appointment pipeline.
- Updated the README and environment templates to reflect the expanded six-target Mescladís monitor set.

## V1.4.227 - 2026-04-24

- Added a Chrome CDP bridge mode to `plus_bridge.js` so the experimental local ChatGPT Plus flow can attach to or launch a browser through remote debugging instead of only using the persistent Playwright profile path.
- Exposed CDP bridge flags and scripts in `package.json`, `.env.example`, README, and the admin Image-2 panel so internal users can try a browser-level automation bridge that local agents can drive.
- Kept the official OpenAI API image path unchanged and continued treating the Plus bridge as a separate experimental route.

## V1.4.226 - 2026-04-24

- Added a visible `Plus Bridge（实验）` card in the admin Image-2 area so the local browser bridge can be discovered from the web UI instead of only from the README.
- Kept the new local bridge workflow and the backend bridge receive/latest endpoints intact so the experimental Plus-only path stays separate from the official OpenAI API path.

## V1.4.225 - 2026-04-24

- Added an experimental local ChatGPT Plus bridge script (`plus_bridge.js`) that uses a persistent Playwright profile to submit prompts from a local machine, capture the rendered image artifact, and optionally upload the result to a server endpoint.
- Added backend bridge receive/latest endpoints under `/persona-api/image-lab/bridge/*` so the local bridge can hand results back to the server without storing image files long-term.
- Documented the bridge workflow in `.env.example`, `package.json`, and `README.md` so internal users can bootstrap a Plus-only automation path while keeping the official OpenAI API route intact.

## V1.4.223 - 2026-04-24

- Tightened the top navigation spacing and turned the mobile bottom nav into a five-slot layout so `image-2` stays visible on narrower screens instead of wrapping out of view.
- Kept the `image-2` entry between Mind and Favorites in the desktop header and did not change the Image Lab flow itself.

## V1.4.222 - 2026-04-24

- Added the `image-2` entry to the mobile bottom navigation so the Image Lab is visible on the `/persona/` homepage in mobile layout too.
- Kept the desktop top navigation placement from the previous revision and did not change the generation flow itself.

## V1.4.221 - 2026-04-24

- Added a top-level `image-2` navigation entry between Mind and Favorites so the internal Image Lab page is visible from the main header.
- Kept the backend image-generation flow unchanged and only adjusted the frontend entry point placement.

## V1.4.220 - 2026-04-24

- Added an internal Image Lab page for GPT Image testing with prompt, size, quality, and output format controls.
- Wired a backend image-generation endpoint that reads `OPENAI_API_KEY` and `OPENAI_IMAGE_MODEL` from environment variables and returns base64 image data without persisting files.
- Added whitelist validation, lightweight internal-user placeholder checks, and friendly error handling so failures do not expose stack traces to the browser.

## V1.4.219 - 2026-04-22

- Added CSV batch-profile support to the Montjuic autofill monitor so the 200-contact import file can be used directly instead of converting into JSON by hand.
- Set the Montjuic CSV path to `montjuic_profiles_template.csv` by default and documented that CSV takes precedence over the JSON fallback.

## V1.4.218 - 2026-04-22

- Added a local `montjuic_profiles_template.csv` file at the repository root so batch-contact imports have a concrete path to start from.
- Kept the Montjuic autofill monitor logic unchanged while providing a simple CSV skeleton for profile batches.

## V1.4.217 - 2026-04-22

- Tightened the Montjuic autofill monitor so it now matches the eight real contact fields by label rather than by page order, which makes surname, given name, email, phone, full address, document number, nationality, and birth date fill independently even when the page reorders them.
- Added select-aware and date-aware field handling plus post-fill verification so the monitor can confirm that nationality and birth date were really filled instead of just assuming a click succeeded.

## V1.4.216 - 2026-04-22

- Added a separate Montjuic appointment watcher that can detect an `OPEN` Google Calendar booking page and batch-fill the contact form from saved templates without touching the existing Google and AgendaPro monitors.
- Exposed a `npm run montjuic:monitor` entrypoint plus new `MONTJUIC_*` environment variables for the target URL, batch profiles, optional qclaw alert file, and optional submission control.

## V1.4.215 - 2026-04-22

- Set the AgendaPro alert file path in both `.env` and `.env.example` so `agendapro_monitor.js` now knows to write events to `/Users/chanzi/.qclaw/workspace-agent-be2ecf0c/agendapro_alert.txt` for the new qclaw watcher.
- Wrote a one-time synthetic AgendaPro `ERROR` alert into the watched file to verify the new push path end-to-end without using a real booking result.

## V1.4.214 - 2026-04-22

- Reset the AgendaPro local state baseline so the monitor no longer carries forward the previously misclassified `OPEN` snapshots for the three Fundación Ibn targets.

## V1.4.213 - 2026-04-22

- Tightened the AgendaPro date extractor so it no longer treats weekday navigation labels as appointment dates, which was causing false `OPEN` alerts on pages that still cannot actually be booked.

## V1.4.212 - 2026-04-22

- Reworked the AgendaPro double-`Agendar ahora` step so the monitor re-resolves the booking root after the first click, uses `noWaitAfter` on clicks, and falls back cleanly when the second click lands on a replaced frame or navigation-heavy page.

## V1.4.211 - 2026-04-22

- Switched the AgendaPro entry step to the real `Agendar servicio` button surfaced by the live page snapshot, keeping `Ver horario` only as a fallback before the existing `Agendar ahora` and availability expansion flow.

## V1.4.210 - 2026-04-22

- Shortened the AgendaPro click helper timeouts and added a quick existence check before each click so a missing `Ver horario` or booking action can fail fast instead of stalling the whole round.

## V1.4.209 - 2026-04-22

- Added lightweight flow-stage logs around `Ver horario`, `Agendar ahora`, and `Ver todas las fechas disponibles` so we can see exactly which step of the AgendaPro booking path is stalling or failing on the real pages.

## V1.4.208 - 2026-04-22

- Added an initial `Ver horario` click to the AgendaPro flow so the monitor can enter the booking area before attempting the double `Agendar ahora` path, while still avoiding `Ver sucursal`.

## V1.4.207 - 2026-04-22

- Added a frame-level snapshot to the AgendaPro `UNKNOWN` debug path so we can see which frame actually carries the booking text when the outer page does not expose any actionable date signals.

## V1.4.206 - 2026-04-22

- Added a compact AgendaPro button snapshot to the `UNKNOWN` debug path so we can see which actionable labels the booking area actually exposes when the flow still fails to classify.

## V1.4.205 - 2026-04-22

- Relaxed the AgendaPro click helpers so `Agendar ahora` and `Ver todas las fechas disponibles` are scrolled into view and clicked instead of being skipped immediately when they are not already visible in the first viewport.

## V1.4.204 - 2026-04-22

- Added a longer initial wait before searching for the AgendaPro booking flow and re-resolved the booking root after the click sequence so the monitor is less likely to inspect the page before the booking widget has finished rendering.

## V1.4.203 - 2026-04-22

- Added a narrow AgendaPro debug log that only prints when the page still ends up `UNKNOWN`, making it easier to see whether the booking frame or the extracted text is still missing the actual availability markers.

## V1.4.202 - 2026-04-22

- Fixed the AgendaPro probe's final text classification step so it now uses the booking-frame text variable consistently after the new signal-based extraction path.

## V1.4.201 - 2026-04-22

- Improved the AgendaPro booking-frame resolver so it scores candidate frames instead of stopping at the first match, which helps avoid picking outer wrapper frames that still contain navigation noise.
- Restricted AgendaPro date detection to the booking frame's interactive elements and tightened the candidate filters so weekday nav labels and footer noise are much less likely to be treated as real appointment dates.

## V1.4.200 - 2026-04-22

- Restricted the AgendaPro monitor to the detected booking iframe so it no longer mixes in top-level navigation or footer text when extracting dates.
- Tightened date detection so only real calendar dates count: numeric dates still work, and weekday names now only count when they stay attached to a day number on the same line.

## V1.4.199 - 2026-04-22

- Improved the AgendaPro classifier so it merges text from the page and every frame before deciding whether the booking flow is `OPEN`, `FULL`, or `UNKNOWN`.
- Treated booking-flow markers such as `Agendar ahora`, `Ver todas las fechas disponibles`, and `No hay horas disponibles para esta selección` as full-page signals so iframe-based pages are less likely to fall through to `UNKNOWN`.

## V1.4.198 - 2026-04-22

- Fixed the AgendaPro probe so the `opened` flag is actually captured after the `Ver todas las fechas disponibles` click instead of being referenced before assignment.
- Kept the three Fundación Ibn URLs and iframe-based booking flow intact while repairing the status classification bug that affected the first real probe run.

## V1.4.197 - 2026-04-22

- Gave the three AgendaPro Fundación Ibn targets unique display names so the AgendaPro monitor can keep separate state for each professional URL instead of rejecting duplicate names.
- Kept the Google Calendar monitor and health daemon unchanged while fixing only the AgendaPro configuration layer needed for multi-target testing.

## V1.4.196 - 2026-04-22

- Tightened the AgendaPro post-click waits so the monitor waits for booking text to settle instead of relying on `domcontentloaded` after each `Agendar ahora` / `Ver todas las fechas disponibles` click.
- Kept the iframe-based flow intact and avoided touching `Ver sucursal`, but made the expansion flow more tolerant of pages that re-render their content without a full navigation.

## V1.4.195 - 2026-04-22

- Upgraded the AgendaPro monitor to search the page frames for the real booking area first, so it can work inside the iframe that holds the reservation flow without touching `Ver sucursal`.
- Kept the double `Agendar ahora` click path and `Ver todas las fechas disponibles` expansion path intact, but now they run in the detected booking frame when that frame exists.

## V1.4.194 - 2026-04-22

- Updated the AgendaPro monitor to follow the real booking flow more closely by clicking `Agendar ahora` twice with a refresh settle in between before it looks for `Ver todas las fechas disponibles`.
- Kept the existing Google Calendar monitor and health daemon unchanged while tightening only the AgendaPro branch that needs the extra click path.

## V1.4.193 - 2026-04-22

- Populated the AgendaPro monitor with the three Fundación Ibn professional URLs that were supplied, keeping the Google Calendar monitor and health daemon untouched.
- Kept all three AgendaPro targets under the same dedicated AgendaPro monitor branch so the new site can be exercised without changing the existing appointment pipelines.

## V1.4.192 - 2026-04-22

- Relaxed the new AgendaPro monitor so it tries `Ver todas las fechas disponibles` before deciding the page is truly full, which better matches pages that hide future dates behind an expansion link.
- Allowed the AgendaPro monitor to run with one, two, or three configured targets so the first booking page can be added and tested independently before the other two are filled in.

## V1.4.191 - 2026-04-22

- Added a separate AgendaPro monitor for booking pages that expose the `Ver todas las fechas disponibles` flow, leaving the Google Calendar monitor and health daemon untouched.
- The new monitor clicks the expansion link when present, extracts visible dates and times, and emits normalized `EVENT_JSON:` updates only when the open slot set changes.
- Preloaded the Fundação Iban booking page as the first AgendaPro target in `.env.example` so the new monitor can be tried immediately without disturbing the existing appointment stack.

## V1.4.190 - 2026-04-22

- Reduced the health daemon cadence from 10 minutes to 60 seconds so a hung appointment producer is detected much sooner.
- Clarified that the health alert reuses the same file-to-qclaw-to-Telegram path as normal monitor alerts unless an explicit webhook is configured.

## V1.4.189 - 2026-04-22

- Added a lightweight heartbeat file writer to `monitor.js` so the producer records a fresh liveness snapshot on startup and each polling round.
- Added a separate resident health daemon that checks the heartbeat every 10 minutes and only writes an `ERROR` alert into `ALERT_FILE_PATH` when the heartbeat goes stale, keeping normal checks silent.
- Added macOS launchd and shell wrapper templates for the health daemon plus a `npm run health:daemon` entrypoint so process-down alerts can run independently of the main appointment monitor.

## V1.4.188 - 2026-04-22

- Switched the resident monitor launcher to `node --input-type=module -e "await import('./monitor.js')"` because that entrypoint is the one that reliably starts Playwright in this environment.
- Kept the restart loop and non-fatal file-write handling, so the resident process can recover if the child exits later.

## V1.4.187 - 2026-04-22

- Restored the Playwright-based appointment probe after the pure `fetch` path proved unable to authenticate to the slots RPC.
- Kept the launch hardening and non-fatal alert-file handling from the recent stability work, so the monitor still fails softer than before while using the known-good data path.

## V1.4.186 - 2026-04-22

- Removed the Chromium dependency from the appointment monitor and switched the producer to a pure Node.js `fetch` flow.
- The monitor now resolves the canonical appointment URL from the fetched HTML and queries the slots RPC directly, which avoids the macOS launchd/Chromium bootstrap crash path entirely.

## V1.4.185 - 2026-04-22

- Restored the monitor to a bash wrapper under launchd but now clear `XPC_SERVICE_NAME` before starting Node so Chromium can launch without the bootstrap rendezvous crash.
- Kept the restart loop and non-fatal alert-file handling in place so a transient exit does not leave the producer offline.

## V1.4.184 - 2026-04-22

- Switched the macOS monitor LaunchAgent to execute `node monitor.js` directly instead of going through a shell wrapper.
- This avoids the shell-layer environment mismatch that was tripping Chromium's bootstrap rendezvous on startup.

## V1.4.183 - 2026-04-22

- Fixed the macOS monitor wrapper so `set -e` no longer aborts the restart loop when `monitor.js` exits nonzero.
- This lets the wrapper actually keep retrying instead of dying with the child process and is the main change that makes the monitor resident.

## V1.4.182 - 2026-04-22

- Made the monitor tolerate alert-file write failures at startup and during event emission instead of exiting the whole process.
- This prevents a missing or temporarily inaccessible `ALERT_FILE_PATH` from killing the producer before it can continue monitoring Google Calendar.

## V1.4.181 - 2026-04-22

- Wrapped the macOS monitor launcher in a restart loop so a transient `monitor.js` exit does not leave the producer offline.
- Added a top-level fatal error handler to `monitor.js` so startup failures are logged cleanly before the wrapper restarts the process.

## V1.4.180 - 2026-04-22

- Added a macOS launchd entrypoint for the appointment monitor so the producer can stay resident without depending on a live terminal session.
- Added a small `run_monitor.sh` wrapper plus a `com.tokendancer.monitor.plist` template that keeps `monitor.js` alive and logs its output to `monitor_runtime.log`.

## V1.4.179 - 2026-04-22

- Rolled the monitor cadence back to the earlier peak/off-peak polling schedule so the runtime matches the pre-15-second behavior again.
- Removed the per-round schedule-ID caching change so each polling round returns to resolving the canonical appointment page before probing slots.
- Kept the canonical schedule-ID fix from the earlier RPC work, so the monitor still resolves the correct appointment page before calling the slots RPC.

## V1.4.178 - 2026-04-22

- Cached each target's canonical schedule ID and stopped reloading the Google appointment page on every polling round.
- Kept the flat 15-second cadence, but removed the per-round navigation overhead that was stretching wall-clock detection well past a minute.

## V1.4.177 - 2026-04-22

- Changed the monitor cadence to a flat 15-second interval all day so there is no peak/off-peak drift while testing response latency.
- Aligned `.env`, `.env.example`, and the README with the new constant polling cadence so the runtime and docs stay in sync.

## V1.4.176 - 2026-04-22

- Fixed schedule ID extraction so the monitor resolves the canonical appointment URL before calling the slots RPC.
- Kept the full-range RPC snapshot approach intact, but removed the false all-target `ERROR` caused by reading the page URL too early.

## V1.4.175 - 2026-04-22

- Rebuilt the appointment monitor around a single full-range RPC snapshot per round, removing the segmented day-click fallback and all guess-based FULL/UNKNOWN logic.
- Simplified the runtime and env surface so the producer now only keeps the full snapshot diff path needed for precise global monitoring.

## V1.4.174 - 2026-04-22

- Reduced the monitor's default concurrent scan rounds back to `1` so the browser stops getting overloaded and the monitor can finish rounds reliably again.
- Updated the docs and env example to treat extra overlap as an optional tuning knob instead of the default operating mode.

## V1.4.173 - 2026-04-22

- Fixed the monitor startup order so `SCAN_TIMEZONE` is initialized before the date-segment window is built.
- Kept the direct alert-file write path and the qclaw watcher event handling fix in place so the file handoff can actually run after startup.

## V1.4.172 - 2026-04-22

- Changed the appointment monitor to write the alert file directly instead of renaming a temporary file, so the file watcher sees a straightforward modify event.
- Hardened the qclaw watchdog to react to created, moved, and modified file events instead of only `on_modified`, which makes the file-handoff path work again for atomic replacements.

## V1.4.171 - 2026-04-22

- Added a macOS launchd template plus a small launcher script so the qclaw alert watcher can run as a resident process instead of a cron job.
- Documented the daemon-based replacement path alongside `npm run alert:daemon` so local file handoff can stay alive without agent re-entry delays.

## V1.4.170 - 2026-04-22

- Added a standalone alert daemon that watches `ALERT_FILE_PATH` continuously so qclaw can receive file-based events without cron drift or agent re-entry delays.
- Exposed `npm run alert:daemon` as the resident file-watcher entrypoint and documented how to use it alongside the existing appointment monitor.

## V1.4.169 - 2026-04-22

- Added overlapping scan-round concurrency so the monitor can keep 3-4 rounds in flight and continue covering future segments while earlier rounds are still running.
- Kept weekend-date skipping, RPC fast path, and fallback scan behavior intact, but now the scheduler can ramp up to a small concurrent pipeline instead of waiting for each round to finish before launching the next one.

## V1.4.168 - 2026-04-22

- Kept the monitor running every day while filtering weekend dates out of the monitored appointment-date list, so the runtime loop stays alive but Saturday and Sunday are never probed.
- Preserved the RPC fast path, fallback scan, and file handoff behavior while separating runtime liveness from which appointment dates get scanned.

## V1.4.167 - 2026-04-22

- Relaxed the scan gate so the monitor now skips only Madrid-time weekends; weekdays remain active all day to avoid missing unexpected releases outside office hours.
- Kept the RPC fast path, fallback scan, and file handoff behavior unchanged while removing the over-restrictive weekday-hours gate.

## V1.4.166 - 2026-04-22

- Added a Madrid-time scan gate so the monitor stays alive on weekends and off-hours but skips page probes outside work windows.
- Kept the RPC fast path and fallback scan intact, while making the round scheduler honor `SCAN_TIMEZONE` for workday-only execution.

## V1.4.165 - 2026-04-22

- Narrowed the RPC fast path so it only short-circuits when it actually returns an `OPEN` slot list; ambiguous `FULL` / `UNKNOWN` RPC results now fall back to the slower but more reliable date-click scan.
- Added an `RPC` trace log so it is easier to see whether a round used the fast path or dropped back to the fallback probe.

## V1.4.164 - 2026-04-22

- Switched the monitor's primary probe from day-by-day button clicking to the appointment page's direct `ListAvailableSlots` RPC, which returns the slot epochs for the monitored range much faster.
- Kept the original date-click fallback in place for resilience, but now the fast path should cover the full range more accurately and with far less round time.
- Added a dedicated `SLOT_TIMEZONE` setting so the RPC slot epochs render into stable human-readable appointment strings.

## V1.4.163 - 2026-04-22

- Reordered the segmented appointment scan so the rounds prioritize the 2-day windows closest to the current date in `MONITOR_TIMEZONE`, which reduces navigation churn on the pages that matter most right now.
- Shortened the page post-load and day-selection waits so each probe round finishes faster while keeping the existing event contract and slot extraction logic intact.

## V1.4.162 - 2026-04-22

- Reused browser pages per target instead of creating and closing a new page on every probe, reducing the overhead of repeated page startup during monitoring.
- Kept the segmented date scan and noise filtering intact so the faster monitor still produces the same event contract.

## V1.4.161 - 2026-04-22

- Made month navigation more tolerant of slow-loading pages by retrying when the displayed month text has not rendered yet instead of bailing out early.
- Kept the segmented scan and noise filtering in place so the faster probe stays more reliable under concurrent page loads.

## V1.4.160 - 2026-04-22

- Filtered bare `02:00` style noise from slot extraction so the monitor keeps only likely appointment times instead of treating body text artifacts as real availability.
- Kept the 2-day segmented scan and 15-second cadence so the monitor stays fast while producing cleaner slot lists.

## V1.4.159 - 2026-04-22

- Reworked the appointment probe to scan the monitored range in 2-day segments and rotate those segments each polling round so the monitor stays within the 15-second cadence.
- Expanded the monitored date window to `2026-04-22` through `2026-06-15` and updated the docs and env defaults to match the new segmented scan strategy.

## V1.4.158 - 2026-04-22

- Hardened slot extraction so the appointment monitor now retries after a longer post-click wait and falls back to a broader DOM scan when visible buttons do not expose the newly added time slot.
- Kept the existing target list, date window, and event contract unchanged while improving the chance of catching newly added appointments on an already open day.

## V1.4.157 - 2026-04-22

- Updated only the Mescladís test appointment target to the new Google Calendar link while leaving the five production links and all monitor behavior unchanged.

## V1.4.156 - 2026-04-22

- Seeded the qclaw alert file at monitor startup so the watched file exists immediately even before the first `OPEN` event arrives.
- Kept the file watcher semantics unchanged by still writing real alert content only when an `OPEN` event is emitted.

## V1.4.155 - 2026-04-22

- Fixed the monitor target validation so the script accepts the current 1 test target plus 5 production targets instead of crashing on a 6-entry target list.
- Kept the updated test-link and qclaw file-handoff configuration intact while making the local monitor startable again.

## V1.4.154 - 2026-04-22

- Set the local alert file path in the runtime environment so the monitor can actually write to the qclaw-watched file instead of leaving `ALERT_FILE_PATH` empty.
- Kept the test target refresh and monitoring range intact while fixing the file handoff configuration that qclaw depends on.

## V1.4.153 - 2026-04-22

- Updated the test appointment monitor target to the new Google Calendar appointment link so the same probe flow now runs against the latest test page.
- Kept the production appointment links, date window, and file handoff behavior unchanged while refreshing the test target in both runtime and example environment files.

## V1.4.152 - 2026-04-22

- Expanded the monitor scope to include the test appointment page alongside the five production appointment links so both paths use the same booking-flow probe.
- Extended the monitored date window to cover `2026-04-23` through `2026-06-10`, keeping the test target and the real targets on the same inspection logic.
- Kept local file handoff support in place so the appointment monitor writes a concise alert summary and the raw event JSON into a watched file whenever an `OPEN` event is emitted.

## V1.4.151 - 2026-04-22

- Added local file handoff support so the appointment monitor writes a concise alert summary and the raw event JSON into a watched file whenever an `OPEN` event is emitted.
- Exposed `ALERT_FILE_PATH` alongside the existing webhook settings so qclaw can consume either a file trigger or an HTTP endpoint.

## V1.4.150 - 2026-04-22

- Upgraded the appointment probe to follow the real booking flow by checking monitored calendar days and then clicking into any open day to read its time buttons.
- Added `MONITOR_DAYS` so the current 22-24 test window is explicit and configurable, and prefixed extracted slots with the day number for clearer change tracking.

## V1.4.149 - 2026-04-22

- Hardened the monitor deploy script so Linux browser dependencies are installed system-wide while Chromium itself is installed under the `ubuntu` user cache, matching the systemd service account.
- Kept the monitor service active after deployment by aligning the install path with the runtime user and avoiding the root-cache mismatch.

## V1.4.148 - 2026-04-22

- Added an always-on systemd service for the appointment monitor so it can run 24/7 on the server with automatic restart.
- Added optional qclaw webhook delivery for every emitted `EVENT_JSON` payload, controlled by `QCLAW_WEBHOOK_URL` and `QCLAW_WEBHOOK_SECRET`.
- Added a dedicated deploy script for the monitor service and documented the server setup path in the README.

## V1.4.147 - 2026-04-22

- Made the peak/off-peak polling window timezone-aware by evaluating the hour in `MONITOR_TIMEZONE` instead of relying on the host system clock.
- Defaulted the monitor timezone to `Asia/Shanghai` so the 08:00 to 21:00 rule stays aligned with the operator's local schedule.

## V1.4.146 - 2026-04-22

- Added time-of-day polling control to the appointment monitor so it now sleeps `30s` between rounds from 08:00 through 20:59 and `60s` otherwise.
- Exposed the peak-window settings in `.env` and `.env.example` so the active polling window can be tuned without touching code.

## V1.4.145 - 2026-04-22

- Added the English `No availability during these days` appointment-page phrase to the monitor's `FULL` detection so the April 22-24 no-slot state is classified correctly.
- Kept the same event contract and admin-only presentation while making the monitor match the live Google Calendar wording more accurately.

## V1.4.144 - 2026-04-22

- Populated the Mescladís appointment monitor with the five provided Google Calendar appointment links in both `.env.example` and the runtime `.env` so the script can run immediately.
- Kept the admin-only presentation intact while updating the monitor's active target configuration for the server-side deployment.

## V1.4.143 - 2026-04-22

- Moved the appointment monitor into the admin surface by adding a backend-only monitor card to the `/admin` page and documenting the server-side script location and launch flow there.
- Restricted the `/admin` route to authenticated admins so regular frontend users no longer see or enter the admin panel.
- Kept the standalone Playwright monitor itself separate from the public UI while preserving the normalized `EVENT_JSON:` output contract.

## V1.4.142 - 2026-04-22

- Added a standalone Node.js + Playwright monitor for five Google Calendar appointment pages that emits normalized `EVENT_JSON:` lines only when status or open-slot changes occur.
- Persisted the last observed state in `state.json`, separated ordinary check logs from event logs, and kept the monitor isolated from any direct notification delivery.
- Documented the new monitor workflow in the root README and shipped a matching `.env.example` for the five target URLs plus polling controls.

## V1.4.141 - 2026-04-19

- Added an optional MBTI / zodiac style distillation layer to the creation flow so users can pick one, both, or neither without affecting the underlying create path.
- Introduced a shared `style_profile` runtime that reads MBTI / zodiac traits, maps them into compact style dimensions, and keeps the result as a soft answer-gating layer instead of a direct stereotype prompt.
- Threaded the distilled style profile into create drafts, persona prompts, self-unified layers, and saved seed summaries so the chosen气质 stays visible and reusable after creation.

## V1.4.140 - 2026-04-19

- Reworked the `Create` landing page into a horizontal main-path switcher so the five primary routes now sit in a single row and only the selected path is shown at once.
- Kept the existing create-path content intact while removing the old stacked accordion feel, making the page read more like a focused selector than a long scroll of sections.
- Preserved the underlying create routing and catalog mapping so the UI change stays shallow and reversible.

## V1.4.139 - 2026-04-19

- Integrated `ex-skill` into the intimate-relationship creation flow and renamed the user-facing intimate path from `关系经营 / 自我镜像` toward `前任` so the create catalog, wizard, and saved-persona summaries now use a more direct product label.
- Kept the underlying mode keys and source routing intact for compatibility, while refreshing the visible labels, helper copy, and summary text to better reflect ex-partner memory modeling, relationship memory, and self-mirror review.
- Updated the create catalog metadata and persona summaries so the new `前任` path remains a true create entry rather than a disconnected alias.

## V1.4.138 - 2026-04-19

- Upgraded the `孙宇晨` seed persona to mirror the newer `sun-skill` cognitive framework: added the 14-model mental map, 19 decision heuristics, expression DNA, anti-patterns, honest boundaries, and the five-era evolution timeline.
- Reworked the Sun persona pack to lean harder into crypto strategy, winner-take-all thinking, attention conversion, and hype-with-judgment expression instead of generic business-topic narration.
- Refreshed the Sun persona examples, intro, and metadata so the seed now triggers more reliably on Sun-style perspective requests and produces more structured, higher-signal answers.

## V1.4.137 - 2026-04-19

- Removed the standalone `歌诀` page because it had no live route or navigation entry; the only remaining divination-facing content still lives inside `我该怎么做` and its related result/history flows.
- Kept `我该怎么做` focused on its actual runtime surface: `起卦方式`, `分类`, `时间`, 起卦输入, 连续对话, 历史, 收藏, and hexagram detail viewing.

## V1.4.136 - 2026-04-19

- Tightened every input-facing UI toward a mainstream AI-chat density by lowering shared control heights, trimming composer padding, and reducing the default visual heft of buttons, selects, and textareas.
- Added textarea autosizing so long text wraps and expands naturally instead of starting with overly tall fixed boxes, while keeping the input shells compact on mobile and desktop.
- Applied the same input-density cleanup to `我该怎么回`, `我该怎么做`, the create wizard, and the song-note input so the whole product feels more consistent at the point of typing.

## V1.4.135 - 2026-04-19

- Added login-time cross-device hydration for persona data so Seed favorites, `我该怎么回` history, and `我该怎么做` history now sync from local cache into the signed-in account as soon as the user logs in or auth is restored.
- Kept the existing local fallback behavior intact, but made the account-scoped remote archive the shared source of truth once a user session exists.

## V1.4.134 - 2026-04-19

- Unified the reply-style chat pages into fixed-height H5-friendly shells so output and input now live inside an internal scroll area instead of making the whole page grow vertically.
- Kept `我该怎么回` and `我该怎么做` anchored to the same dialogue-window pattern, with chat content scrolling inside the card and the composer staying pinned at the bottom.
- Added auto-scroll-to-bottom behavior when reopening a saved conversation so chat history lands at the latest turn instead of the top of the thread.

## V1.4.133 - 2026-04-19

- Moved the `我该怎么做` cast selectors to sit directly above the send button inside the persistent input composer, so `起卦方式 / 分类 / 时间` now feel pinned to the input box itself.
- Kept the chat-card layout and the single continuing input intact while making the selector row part of the same bottom dialogue block instead of a separate control strip above the conversation.

## V1.4.132 - 2026-04-19

- Kept the `我该怎么做` cast selectors pinned directly above the bottom input composer so `起卦方式 / 分类 / 时间` now stay attached to the chat box instead of floating as a separate block.
- Tightened the lower composer into a full chat-card surface so the input area reads more like a persistent dialogue window, closer to `我该怎么回`.
- Kept the current cast flow, history, favorites, and result rendering intact while only changing the input-side UI framing.

## V1.4.131 - 2026-04-19

- Reworked `我该怎么做` into a more `我该怎么回`-style chat shell by removing the top question input and keeping only one persistent bottom composer for continuing divination chat.
- Removed the visible “先选大类后，这里会同步显示这一类更适合怎么问。” helper copy and tightened the page around control chips, the result window, and the single chat input.
- Kept the existing cast-mode picker, grouped category picker, time picker, history, and favorites behavior intact while making the page feel less like a form and more like a conversation window.

## V1.4.130 - 2026-04-19

- Reworked `我该怎么做` into a reply-assistant-style chat shell with top-level picker chips for `起卦方式`, `分类`, and `时间`, while keeping the cast flow unchanged under the hood.
- Added bottom-sheet style pickers for cast mode, grouped category selection, and editable cast time, so the mobile UI now feels closer to the `我该怎么回` dialogue layout.
- Moved `我该怎么做` history and favorites into the shared archive window pattern and kept the left hamburger menu focused on `新对话`, `收藏对话`, `历史`, and `收藏`.
- Preserved the existing cast results, follow-up chat, and favorite-hexagram behavior, but tightened the visible UI into a more compact chat-like composition.

## V1.4.129 - 2026-04-19

- Simplified the `个人` page into four equal rounded square cards with no extra explanatory copy, and redirected `我该怎么回` / `我该怎么做` to a shared archive window instead of their full working pages.
- Added a shared `历史 / 收藏` archive route for `我该怎么回` and `我该怎么做`, so both modules can open the same compact history/favorites window while keeping their own records separate.
- Moved `我该怎么做` history and favorites entry points beside `在线起卦`, and added a direct `收藏` action beside the result fold toggle for favoriting the current hexagram.
- Reworked the `我该怎么回` hamburger menu into a smaller action sheet with `新对话`, `收藏对话`, `历史`, and `收藏`, then wired `历史 / 收藏` to the shared archive window.

## V1.4.128 - 2026-04-19

- Reworked the `个人` page into four equal rounded square entry cards arranged in a clover-style 2x2 layout, replacing the old `最近会话` entry with `我该怎么做` and renaming the favorites card copy to `收藏的seed`.
- Synced the top-left `SeedMind` logo background to the same accent-soft color used behind the numbered tags on the personal and favorites cards.

## V1.4.127 - 2026-04-19

- Moved the `我该怎么做` `历史 / 收藏` controls up beside the cast-mode chips so they now match the same rounded spec and stay visible in a cleaner, more consistent position.
- Reworded the first-two-replies soft follow-up nudges for `我该怎么做` so they no longer use obvious AI phrasing like `偏宽 / 往下收`, and now sound more natural with wording closer to `细致 / 明确 / 准确 / 分析 / 判断`.

## V1.4.126 - 2026-04-19

- Tuned the `SeedMind` header logo again so the outer background now sits much closer to the homepage day-mode background, while the inner mark is retinted further toward the warm pink accent palette.
- Renamed the `我该怎么做` relationship category label from `婚姻复合` to `感情复合` in the frontend and added backend compatibility so both the new and old values still route correctly.

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

# V1.4.224
- Added an explicit Image-2 entry inside the admin page so internal users can reach Image Lab without opening `/persona-api/` directly.
- Documented the Image Lab page and API endpoint in the admin workspace entry.

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
