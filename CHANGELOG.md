# Changelog

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
