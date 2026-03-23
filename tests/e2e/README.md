# E2E Smoke Scaffolding

These smoke tests are a contract scaffold for the three primary user journeys:

- Speak Text
- Change Voice
- Clean Recording

They are written for Playwright and intentionally skip unless a live desktop or web preview is available.

## Environment

- `HVS_E2E_URL`: base URL for the running UI preview, usually `http://127.0.0.1:1420`
- `HVS_E2E_RUN=1`: optional opt-in flag for local smoke execution

## Coverage Intention

- Navigate to each primary tab.
- Fill the plain-language controls only.
- Start a job.
- Wait for a visible preview or completion state.
- Verify export affordances are present.

The selectors in `smoke.spec.ts` use stable, user-facing labels so the test remains aligned with the contract even as the internals change.
