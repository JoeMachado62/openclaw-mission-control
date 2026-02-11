# Architecture

## Deep dives

- [Architecture deep dive](architecture/README.md)
- [Gateway protocol](openclaw_gateway_ws.md)

Mission Control is the **web UI + HTTP API** for operating OpenClaw. It’s where you manage boards, tasks, agents, approvals, and (optionally) gateway connections.

> Auth note: **Clerk is required for now** (current product direction). The codebase includes gating so CI/local can run with placeholders, but real deployments should configure Clerk.

## Components

- **Frontend**: Next.js app used by humans
  - Location: `frontend/`
  - Routes/pages: `frontend/src/app/*` (Next.js App Router)
- **Backend**: FastAPI service exposing REST endpoints
  - Location: `backend/`
  - App wiring: `backend/app/main.py`
  - API prefix: `/api/v1/*`
- **Database**: Postgres (from `compose.yml`)

## Diagram (conceptual)

```mermaid
flowchart LR
  U[User / Browser] -->|HTTP| FE[Next.js Frontend :3000]
  FE -->|HTTP /api/v1/*| BE[FastAPI Backend :8000]

  BE -->|SQL| PG[(Postgres :5432)]

  BE -->|WebSocket (optional)| GW[OpenClaw Gateway]
  GW --> OC[OpenClaw runtime]
```

## Key request/data flows

### UI → API
1. Browser loads the Next.js frontend.
2. Frontend calls backend endpoints under `/api/v1/*`.
3. Backend reads/writes Postgres.

### Auth (Clerk)
- Frontend enables Clerk when a publishable key is present/valid.
- Backend verifies Clerk JWTs using **`CLERK_JWKS_URL`**.

See also:
- Frontend auth gating: `frontend/src/auth/*` (notably `frontend/src/auth/clerkKey.ts`).
- Backend auth: `backend/app/core/auth.py`.

### Agent access (X-Agent-Token)
Automation/agents can use the “agent API surface”:
- Endpoints under `/api/v1/agent/*`.
- Auth via `X-Agent-Token`.

See: `backend/app/api/agent.py`, `backend/app/core/agent_auth.py`.
