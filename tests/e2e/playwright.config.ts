import { defineConfig } from "@playwright/test";

const baseURL = process.env.HVS_E2E_URL ?? "http://127.0.0.1:1420";

export default defineConfig({
  testDir: ".",
  timeout: 30_000,
  retries: 0,
  use: {
    baseURL,
    trace: "on-first-retry",
  },
});
