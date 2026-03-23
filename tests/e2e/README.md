# E2E Smoke Scaffolding

These smoke tests are a contract scaffold for the three primary user journeys:

- Speak Text
- Change Voice
- Clean Recording

They are written for Playwright and intentionally skip unless a live desktop or web preview is available.

## Environment

- `HVS_E2E_URL`: base URL for the running UI preview, usually `http://127.0.0.1:1420`
- `HVS_E2E_RUN=1`: optional opt-in flag for local smoke execution

## Before Running

1. Start the UI preview with `npm run dev --workspace @home-voice-studio/desktop`.
2. Set `HVS_E2E_URL` to the preview URL if it is not `http://127.0.0.1:1420`.
3. Set `HVS_E2E_RUN=1` to enable the tests instead of skipping them.

## Coverage Intention

- Navigate to each primary tab.
- Fill the plain-language controls only.
- Start a job.
- Wait for a visible preview or completion state.
- Verify export affordances are present.

The selectors in `smoke.spec.ts` use stable, user-facing labels so the test remains aligned with the contract even as the internals change.

## Run Command

```bash
HVS_E2E_RUN=1 HVS_E2E_URL=http://127.0.0.1:1420 npx playwright test --config tests/e2e/playwright.config.ts
```
