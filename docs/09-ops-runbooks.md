# Ops / runbooks

## Deep dives

- [Deployment](deployment/README.md)
- [Production](production/README.md)
- [Troubleshooting](troubleshooting/README.md)

This page is the operator/SRE entry point. It intentionally links to existing deeper docs to minimize churn.

## “First 30 minutes” incident checklist

1. **Confirm user impact + scope**
   - What is broken: UI, API, auth, or gateway integration?
   - Is it all users or a subset?

2. **Check service health**
   - Backend: `/healthz` and `/readyz`
   - Frontend: can it load? does it reach the API?

3. **Check auth (Clerk) configuration**
   - Frontend: is Clerk enabled unexpectedly? (publishable key set)
   - Backend: is `CLERK_JWKS_URL` configured correctly?

4. **Check DB connectivity**
   - Can backend connect to Postgres (`DATABASE_URL`)?

5. **Check logs**
   - Backend logs for 5xx spikes or auth failures.
   - Frontend logs for proxy/API URL misconfig.

6. **Stabilize**
   - Roll back the last change if available.
   - Temporarily disable optional integrations (gateway) to isolate.

## Backups / restore (placeholder)
- Define backup cadence and restore steps once production deployment is finalized.
