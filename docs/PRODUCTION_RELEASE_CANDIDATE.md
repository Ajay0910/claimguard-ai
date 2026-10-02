# ClaimGuard AI production release candidate

Status as of 2026-10-02: **RELEASE CANDIDATE - BLOCKED BY SPECIFIC ITEMS**. See [HANDOFF.md](../HANDOFF.md) for current verification and the next unfinished item.

## Patient portal API

- `POST /api/portal/submit` accepts multipart form fields `patient_name`, `patient_email`, `patient_phone`, `hospital_bill`, `insurance_policy`, and `rejection_letter`. All three documents are required for cross-document verification. It also requires a stable, high-entropy `X-Portal-Secret`; clients must reuse that value when retrying so the same claim is returned instead of creating duplicate analyses. Each file is limited by `MAX_UPLOAD_SIZE_MB` (25 MB by default), and all files together are limited by `MAX_SUBMISSION_SIZE_MB` (50 MB by default). The combined byte total is checked before persistent files are saved. Bytes are checked against PDF/JPEG/PNG/TIFF signatures and stored under a generated filename.
- A successful response returns `claim_id`, `portal_secret`, `status`, and `tracking_url`. The high-entropy secret is returned once. The database stores only its SHA-256 digest. Patients must save the key; support cannot retrieve it from the database.
- `GET /api/portal/status/{claim_id}` requires `X-Portal-Secret`. Unknown claim IDs and wrong/missing secrets return the same 404 response.
- `GET /api/portal/{claim_id}/appeal` also requires `X-Portal-Secret` and returns a draft only for a completed `MISMATCH_DETECTED` result. It is an AI-assisted draft and must be reviewed before sending.
- `WS /api/portal/ws/claim/{claim_id}` requires the raw secret as the first WebSocket message over WSS. The server sends no claim data before validation. Do not place the secret in a URL.

## Staff API and trusted OIDC proxy

Analysis admission is capped globally by `MAX_PENDING_ANALYSIS_JOBS` (4 by
default, counting pending and running jobs). When full, both portal submission
and staff analysis requests return HTTP 503 with `Retry-After: 30`.

The `/api/upload`, `/api/claims`, `/api/stats`, `/api/analyze`, and `/api/reports` routes require all three trusted proxy values:

- `X-ClaimGuard-Proxy-Token` must match `STAFF_PROXY_SHARED_SECRET`.
- `X-Authenticated-User` must contain a valid user identifier.
- `X-Authenticated-Groups` must contain `STAFF_REQUIRED_GROUP` (`claimguard-staff` by default).

The OIDC gateway must remove incoming copies of these headers and set fresh values only after authentication. Keep the backend proxy secret only in the gateway and Render environment. Public browser access to staff routes should pass through the OIDC gateway; a direct request to the Render origin must not have the proxy secret. Restrict CORS to the exact HTTPS portal and staff origins using `CORS_ALLOWED_ORIGINS`.

## Render deployment settings

The Blueprint now describes one paid web instance, a persistent `/var/data` disk for uploaded evidence, and paid Postgres. Render's free web filesystem is ephemeral and free Postgres expires after 30 days, so they cannot safely retain ClaimGuard production records or uploads ([Render free service limitations](https://render.com/docs/free), [persistent disks](https://render.com/docs/disks)). The Blueprint change may increase cost; no deploy or paid resource was created by this code change.

Before deployment, set these dashboard values:

1. `CORS_ALLOWED_ORIGINS`: comma-separated exact HTTPS frontend origins.
2. `STAFF_PROXY_SHARED_SECRET`: a random secret of at least 32 characters, identical only at the OIDC gateway.
3. The configured provider API key (`OPENAI_API_KEY` for the current Blueprint).
4. Configure OIDC authentication and ensure the gateway strips and replaces the identity/group/proxy headers.
5. Set the portal build's `VITE_API_URL` to the HTTPS Render API origin. The portal uses this direct origin for the WebSocket route; do not put the portal secret in a query string.

The start command runs Alembic migrations before Uvicorn. Startup refuses insecure production configuration; `/api/health` returns 503 when Postgres or persistent upload storage is unavailable. The single-instance disk configuration is intentional: Render persistent disks cannot be shared across multiple service instances ([Render disk limitations](https://render.com/docs/disks)).

## Release gates not proven by repository tests

- Run deployment smoke checks through the real OIDC gateway, including direct-origin bypass attempts and verification of forwarded identity/group claims.
- Run a controlled multi-page VLM test with production-like provider credentials. If no key is configured locally, live-provider behavior must be reported as **NOT VERIFIED**.
- Add and freeze an independently reviewed 50–100-case end-to-end UAT set before using benchmark accuracy as a release metric. The checked-in 35-case dataset is synthetic and its existing runner does not provide a valid accuracy measure.
- Confirm operational retention, deletion, backup/restore, and incident response requirements for uploaded health records before public launch.
- The process-local submission limiter is a supplemental guardrail. Configure request/body-size limits and a global rate limit at the public edge before exposing the portal.
