import { defineConfig, defaultExclude } from "vitest/config";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173
  },
  test: {
    environment: "jsdom",
    exclude: [...defaultExclude, "test/e2e/**", "playwright-report/**"],
    globals: true,
    include: ["test/**/*.{test,spec}.{ts,tsx}"],
    setupFiles: "./test/setup.ts"
  }
});
