# Tokendancer Persona Station

This repository hosts the V1 persona web station for `tokendancer.com/persona/`.

Current scope:

- Official persona showcase homepage
- Persona detail page
- Chat page shell
- Personal hub page
- Backend API prefix under `/persona-api/`
- Git-driven build and deployment workflow

The repo also contains older legacy application files. The persona station lives in the new `frontend/` and `backend/` entrypoints added for V1.

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
