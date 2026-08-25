# Business Workflow Background Worker

Run the canonical workflow consumer as a separate Render Background Worker. Do not run it inside the FastAPI web process.

## Start command

```text
python -m app.workers.business_workflow
```

## Environment contract

The worker must use the same production operation database and schema contract as the backend:

- `DATABASE_URL` — required production operation PostgreSQL connection; never use the Directus content database.
- `DATABASE_ENVIRONMENT=production` — required by schema readiness policy.
- `BUSINESS_WORKFLOW_POLL_SECONDS=5` — optional; accepted range 1–60 seconds.
- `BUSINESS_WORKFLOW_LEASE_SECONDS=900` — optional; accepted range 600–3600 seconds.
- `BUSINESS_WORKFLOW_WORKER_ID` — optional stable instance label; an instance-specific value is generated otherwise.
- Capability-specific secrets already required by the analytical implementations, if any.

Do not copy secret values into this file or the repository. Configure them as Render secrets.

## Pilot capacity

Use one worker instance with one in-process task at a time. Durable database claims and leases remain the ownership authority. Scale-out must be a separate reviewed change.

## Deploy order

1. Deploy the backend revision containing the canonical API and worker code.
2. Confirm backend schema readiness remains current.
3. Create/deploy one Render Background Worker from the same revision and start command above.
4. Confirm the worker start log appears without exception details or secrets.
5. Run one controlled authenticated Business Workflow acceptance and bounded status polling.

No migration, web-service startup hook, or in-memory queue is required.
