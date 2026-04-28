import { defineConfig, devices } from "@playwright/test";

const webServerPort = process.env.PLAYWRIGHT_WEB_SERVER_PORT ?? "5173";
const frontendBaseUrl = process.env.PLAYWRIGHT_BASE_URL ?? `http://localhost:${webServerPort}`;
const backendApiBaseUrl = process.env.E2E_API_BASE_URL ?? "http://localhost:8000";
const browserApiBaseUrl = process.env.VITE_API_BASE_URL ?? "/api";
const reuseExistingServer = process.env.PLAYWRIGHT_REUSE_SERVER == null
  ? !process.env.CI
  : process.env.PLAYWRIGHT_REUSE_SERVER === "1";

export default defineConfig({
  testDir: "./test/e2e",
  fullyParallel: false,
  workers: 1,
  timeout: 60_000,
  reporter: [["list"]],
  use: {
    baseURL: frontendBaseUrl,
    trace: "on-first-retry",
    navigationTimeout: 45_000,
  },
  webServer: {
    command: `yarn dev --host localhost --port ${webServerPort}`,
    url: frontendBaseUrl,
    env: {
      ...process.env,
      VITE_API_BASE_URL: browserApiBaseUrl,
      VITE_API_PROXY_TARGET: backendApiBaseUrl,
    },
    reuseExistingServer,
    timeout: 120_000,
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
