# Home Voice Studio

Home Voice Studio is a local-first desktop app for personal home audio workflows. The product contract is defined in [docs/architecture-contract.md](docs/architecture-contract.md), and the developer bootstrap guidance is in [docs/developer-setup.md](docs/developer-setup.md).

## Current repo shape

- `apps/desktop` for the Tauri + React desktop app
- `services/inference` for the local FastAPI sidecar
- `packages/shared-types` for shared request and response contracts
- `packages/ui` for reusable UI primitives
- `data/profiles`, `data/exports`, and `data/cache` for local-first storage

## Development bootstrap

1. Install the prerequisites listed in [docs/developer-setup.md](docs/developer-setup.md).
2. Bootstrap the local data directories:
   ```bash
   npm run bootstrap
   ```
3. Run the workspace doctor:
   ```bash
   npm run doctor
   ```
4. Prepare local model placeholders:
   ```bash
   npm run bootstrap:models
   ```
5. Inspect workspace status:
   ```bash
   npm run status
   ```
6. Run the current local verification stack:
   ```bash
   python3 scripts/dev.py verify
   ```

## Test Run Now

The current workspace can be tested in layers:

- Frontend and backend verification now via [docs/local-testing.md](docs/local-testing.md)
- Playwright smoke scaffolding in [tests/e2e/README.md](tests/e2e/README.md)
- The packaged desktop app now has a release entrypoint via `npm run package:desktop`, but the bundled sidecar still requires either PyInstaller or an explicit `HVS_SIDECAR_BIN` in [docs/remaining-work.md](docs/remaining-work.md)

## Notes

- The repository is intentionally local-first.
- No cloud dependency is required for the MVP.
- Model-specific integrations remain behind stable interfaces so providers can be swapped later without changing the UI contract.
