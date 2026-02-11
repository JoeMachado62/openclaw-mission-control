# Troubleshooting

## Deep dives

- [Troubleshooting deep dive](troubleshooting/README.md)

This is the high-level troubleshooting entry point (minimal churn).

## Quick triage

### Symptom: frontend loads but shows API errors
- Confirm `NEXT_PUBLIC_API_URL` points to a reachable backend.
- Check backend `/healthz`.

### Symptom: frontend keeps redirecting / Clerk errors
- If you are running locally without Clerk, ensure `NEXT_PUBLIC_CLERK_PUBLISHABLE_KEY` is **unset/blank**.
- See: [repo README Clerk note](../README.md#note-on-auth-clerk).

### Symptom: backend 5xx
- Check DB connectivity (`DATABASE_URL`) and migrations.
- Check backend logs.

## Next
- Promote the most common issues from `docs/troubleshooting/README.md` into this page once we see repeated incidents.
