# Development

## Deep dives

- [Testing guide](testing/README.md)

This is the contributor-focused dev workflow for the Mission Control repo.

## Prereqs
- Docker + Docker Compose
- Node (for the frontend)
- Python (for the backend)

## Common commands
- See `Makefile` for the canonical targets.
- Self-host stack (dev-ish): follow the [Quickstart](02-quickstart.md).

## Local services
- Postgres is provided by Compose (`compose.yml`).

## Debugging tips
- Backend liveness: `GET /healthz`
- Backend routes live under `/api/v1/*` (see `backend/app/main.py`).

## Next (to flesh out)
- Document the exact backend/frontend dev commands used by maintainers (once finalized).
- Add a “how to run tests” pointer to `docs/testing/README.md`.
