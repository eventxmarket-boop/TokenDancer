# qclaw Image Bridge Status Template

Purpose:
- Read-only test only.
- Consume `GET /persona-api/image-lab/bridge/status`.
- Do not modify repository code, config, or generated assets.
- Do not create commits, PRs, or code patches from this probe.

Recommended command:

```bash
cd /Users/chanzi/Desktop/xuedingtoken_latest
python3 backend/scripts/qclaw_image_bridge_status_probe.py --url http://127.0.0.1:8011/persona-api/image-lab/bridge/status
```

Optional watch mode:

```bash
cd /Users/chanzi/Desktop/xuedingtoken_latest
python3 backend/scripts/qclaw_image_bridge_status_probe.py --watch --interval 3 --url http://127.0.0.1:8011/persona-api/image-lab/bridge/status
```

If the bridge is remote, replace the URL with the deployed endpoint:

```bash
python3 backend/scripts/qclaw_image_bridge_status_probe.py --url https://tokendancer.xyz/persona-api/image-lab/bridge/status
```

Expected output fields:
- `mode`
- `transport`
- `stage`
- `message`
- `prompt_length`
- `size`
- `quality`
- `output_format`
- `success`
- `error`
- `events`

Usage note:
- qclaw should treat this as a monitoring/test-only probe.
- qclaw must not edit files, generate patches, or alter the repository while running this template.
