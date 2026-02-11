# API reference (first pass)

## Deep dives

- [Gateway WebSocket protocol (API-ish)](openclaw_gateway_ws.md)

This is a **map** of the Mission Control HTTP API surface. It’s intentionally light-weight for the first pass.

## Base
- Backend service: `backend/app/main.py`
- API prefix: `/api/v1`

## Auth

### User/browser auth (Clerk)
- Used for the human UI.
- Frontend enables Clerk when `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` is set.
- Backend verifies JWTs when `CLERK_JWKS_URL` is configured.

### Agent auth (X-Agent-Token)
- Used by automation/agents.
- Header: `X-Agent-Token: <token>`
- Agent endpoints live under `/api/v1/agent/*`.

## Endpoint groups (routers)
Routers are registered in `backend/app/main.py`:
- `auth_router`
- `agent_router` (agent surface)
- `agents_router`
- `activity_router`
- `gateway_router`, `gateways_router`
- `metrics_router`
- `organizations_router`
- `souls_directory_router`
- `board_groups_router`, `board_group_memory_router`
- `boards_router`, `board_memory_router`, `board_onboarding_router`
- `approvals_router`
- `tasks_router`
- `users_router`

## Examples

### Health
```bash
curl -s http://localhost:8000/healthz
```

### Agent call (example)
```bash
curl -s http://localhost:8000/api/v1/agent/boards \
  -H "X-Agent-Token: $AGENT_TOKEN"
```

## Next
- Add a per-router table of key paths once we standardize which endpoints are “public” vs “internal”.
- If an OpenAPI schema exists/gets added, link it here.
