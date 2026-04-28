import { defineConfig, defaultExclude } from "vitest/config";
import react from "@vitejs/plugin-react";

const apiProxyTarget = process.env.VITE_API_PROXY_TARGET ?? "http://localhost:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    proxy: {
      "/api": {
        target: apiProxyTarget,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, ""),
      },
    },
  },
  test: {
    environment: "jsdom",
    exclude: [...defaultExclude, "test/e2e/**", "playwright-report/**"],
    globals: true,
    include: ["test/**/*.{test,spec}.{ts,tsx}"],
    setupFiles: "./test/setup.ts",
    coverage: {
      provider: "v8",
      reportsDirectory: "./coverage",
      reporter: ["text", "html", "lcov"],
      include: ["src/**/*.{ts,tsx}"],
      exclude: ["src/main.tsx"],
    },
  }
});
