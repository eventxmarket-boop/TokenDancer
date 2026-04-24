# Tokendancer Persona Station

This repository hosts the V1 persona web station for `tokendancer.com/persona/`.

Current scope:

- Official persona showcase homepage
- Persona detail page
- Chat page shell
- Personal hub page
- Backend API prefix under `/persona-api/`
- Git-driven build and deployment workflow

The repo also contains an experimental local ChatGPT Plus bridge for internal image generation tests. It is browser automation, not an official API integration, and only works when a Plus session is already logged in on the local machine.

The persona station lives in the `frontend/` and `backend/` entrypoints only.

## Layout

- `frontend/`: Vite + Vue app for the persona station
- `backend/`: FastAPI app entrypoint and persona data directories
- `deploy/`: build and deployment scripts plus Nginx sample config

## Development

Frontend:

```bash
cd frontend
npm run dev
```

Backend:

```bash
cd backend
uvicorn main:app --reload --port 8011
```

Experimental Plus bridge:

```bash
npm run plus:bridge -- --prompt "a studio portrait of a robot reading a book"
```

Useful flags:

- `--bootstrap` opens a persistent browser so you can log in once.
- `--upload-url` posts the generated base64 payload to a server endpoint after capture.
- `--headless false` keeps the browser visible while debugging.

The bridge writes the rendered image artifact to `.plus_bridge_output/` and prints the same JSON payload to stdout. If you point `--upload-url` at a server endpoint, the bridge will also POST the payload there as a handoff step.

## Appointment Monitor

The repository also includes a standalone Node.js + Playwright monitor that polls the test appointment page plus five Google Calendar appointment schedule pages and emits normalized events only when the full RPC slot snapshot changes.

Setup:

```bash
npm install
npm run install:chromium
cp .env.example .env
```

Edit the test target plus the five `TARGET_*_URL` values in `.env`, then start the monitor:

```bash
npm run monitor
```

Event lines are printed with the `EVENT_JSON:` prefix so OpenClaw can consume them directly.

If you want the monitor to push events directly to qclaw, set:

- `TARGET_TEST_URL` for the test appointment page
- `MONITOR_TIMEZONE` to control the workday gate for scanning, defaulting to `Europe/Madrid`
- `SLOT_TIMEZONE` to control how slot epochs are rendered in event output, defaulting to `Europe/Madrid`
- `QCLAW_WEBHOOK_URL`
- `QCLAW_WEBHOOK_SECRET` if qclaw expects a shared secret header
- `ALERT_FILE_PATH` if qclaw is watching a local file instead of a webhook
- `MONITOR_START_DATE` and `MONITOR_END_DATE` to set the monitored date range, defaulting to `2026-04-22` through `2026-06-15`
- `MONITOR_HEARTBEAT_FILE_PATH` to store the producer heartbeat JSON for health checks, defaulting to `monitor_heartbeat.json`

If you want the monitor to self-report when it has hung or stopped updating, run the separate health daemon on the same machine:

```bash
npm run health:daemon
```

The health daemon checks `MONITOR_HEARTBEAT_FILE_PATH` every 60 seconds by default. If the heartbeat goes stale, it writes an `ERROR` payload into `ALERT_FILE_PATH`, which qclaw can forward as a process-down notification. Fresh heartbeats stay silent.

That process-down alert uses the same file-to-qclaw-to-Telegram path as normal monitor alerts by default. The health daemon does not need its own Telegram bot config unless you explicitly set `NOTIFY_WEBHOOK_URL`.

On macOS, you can also install `deploy/com.tokendancer.monitor-health.plist` and use `deploy/run_monitor_health_daemon.sh` as the resident entrypoint for that health watcher.

If qclaw is consuming a local file and you want lower-latency delivery than cron-based polling, run the standalone alert daemon on the same machine:

```bash
npm run alert:daemon
```

The daemon watches `ALERT_FILE_PATH` continuously, deduplicates file changes by hash, and emits the parsed event immediately when a new `OPEN` or `ERROR` payload lands. This avoids cron drift and the extra wait between agent runs.

For macOS, you can also install the launchd template in `deploy/com.tokendancer.qclaw.alert-daemon.plist` and use `deploy/run_qclaw_alert_daemon.sh` as the resident process entrypoint. That is the cron replacement path for qclaw-style local watchers.

If you want the appointment producer itself to stay resident on macOS instead of relying on a terminal session, use the monitor launchd template in `deploy/com.tokendancer.monitor.plist`. The wrapper clears `XPC_SERVICE_NAME`, restarts the import-based `monitor.js` entrypoint on failure, and keeps the producer resident.

Then install and start the systemd service:

```bash
sudo bash deploy/deploy_monitor.sh
sudo systemctl status tokendancer-monitor.service
```

Polling rule:

- The monitor stays active every day and polls the full RPC slot window on every round.
- 08:00 to 20:59: `30s`
- 21:00 to 07:59: `60s`
- Time window is evaluated in `MONITOR_TIMEZONE` and defaults to `Asia/Shanghai`
- The producer writes a heartbeat JSON file on startup and every round
- `monitor_health_daemon.js` checks the heartbeat on a 60-second cadence
- If the heartbeat is stale, the daemon emits an `ERROR` alert into `ALERT_FILE_PATH`
- If the heartbeat is fresh, it stays silent and does not disturb Telegram

File handoff for qclaw:

1. Set `ALERT_FILE_PATH` to the exact file qclaw watches.
2. Run the monitor on the same machine or mounted workspace as qclaw.
3. When an `OPEN` event occurs, the monitor writes a short summary plus the raw JSON into that file.
4. Run `npm run alert:daemon` on the same machine as qclaw if you want a resident file watcher instead of cron-based polling.
5. On macOS, prefer the launchd template in `deploy/com.tokendancer.qclaw.alert-daemon.plist` so the watcher stays alive after login without cron.
6. qclaw can then forward the content when the file changes.

Monitoring window:

- The current date range is `2026-04-22` through `2026-06-15`
- The test page and the five real links use the same full-range RPC snapshot flow
- The producer no longer uses the old segmented fallback scan or per-day page clicking
- If the RPC returns slots, the target is `OPEN`; if it returns no slots, the target is `FULL`; if RPC fails, the target is `ERROR`

## Montjuic Autofill Monitor

For Google Calendar appointment pages that move from slot detection into a contact-information form, there is a separate Montjuic watcher that can keep polling, detect an `OPEN` state, and then batch-fill the booking form with saved contact templates.

Setup:

```bash
cp .env.example .env
```

Set the `MONTJUIC_*` values in `.env`, especially:

- `MONTJUIC_TARGET_URL` for the booking page
- `MONTJUIC_PROFILES_CSV_PATH` for the batch CSV file, defaulting to `montjuic_profiles_template.csv`
- `MONTJUIC_PROFILES_JSON` for one or more contact templates
- `MONTJUIC_ALERT_FILE_PATH` if qclaw should watch a local alert file
- `MONTJUIC_AUTO_SUBMIT=false` by default so the script only fills the form unless you explicitly allow submission

Run it with:

```bash
npm run montjuic:monitor
```

The Montjuic monitor:

- uses the same Google appointment RPC snapshot to detect `OPEN` / `FULL` / `ERROR`
- treats the first `OPEN` snapshot as a trigger, so it can autofill immediately instead of waiting for a later state change
- fills the common booking fields by label, including surname, given name, email, phone, full address, document number, nationality, and birth date
- supports batch profiles, so you can queue several contact templates and let the script fill them one after another
- reads batch profiles from CSV first when `MONTJUIC_PROFILES_CSV_PATH` points to a file, then falls back to `MONTJUIC_PROFILES_JSON`
- keeps the current Google Calendar monitor, AgendaPro monitor, and health daemon untouched

## AgendaPro Monitor

There is also a separate AgendaPro monitor for sites that use the `Ver todas las fechas disponibles` flow.

This path is independent from the Google Calendar monitor and does not change the health daemon or qclaw file watcher.

Setup:

```bash
cp .env.example .env
```

Set the `AGENDAPRO_*` values in `.env`, then run:

```bash
npm run agendapro:monitor
```

The AgendaPro monitor:

- opens each `AGENDAPRO_TARGET_*_URL`
- clicks `Agendar ahora` twice when the button appears, waiting for the page refresh between clicks
- searches the page frames for the actual booking area and works inside that iframe when needed
- clicks `Ver todas las fechas disponibles` when present, even if the current selection says no hours are available
- waits for the booking text to settle after each click instead of treating `domcontentloaded` as the only completion signal
- merges text from the page and every frame before classifying the result, so iframe-based booking widgets are less likely to fall through to UNKNOWN
- checks whether the page contains `No hay horas disponibles` / `No hay disponibilidad` after expansion
- extracts visible dates and times from the expanded page
- emits `EVENT_JSON:` only when the status changes or the open slot set changes

The first target is prefilled with the Fundación Ibn professional booking page you sent.
