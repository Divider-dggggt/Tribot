import { defineConfig, defaultExclude } from "vitest/config";
import react from "@vitejs/plugin-react";
import type { PluginOption } from "vite";

const apiProxyTarget = process.env.VITE_API_PROXY_TARGET ?? "http://localhost:8000";
const coveragePlugins: PluginOption[] = [];

if (process.env.VITE_COVERAGE === "true") {
  try {
    const { default: istanbul } = await import("vite-plugin-istanbul");
    coveragePlugins.push(istanbul({
      exclude: ["test/**"],
      extension: [".ts", ".tsx"],
      requireEnv: true,
      checkProd: false,
    }));
  } catch {
    throw new Error(
      "VITE_COVERAGE=true but vite-plugin-istanbul is missing. Run yarn install and restart the frontend container."
    );
  }
}

export default defineConfig({
  plugins: [react(), ...coveragePlugins],
  server: {
    host: true,
    port: 5173,
    proxy: {
      "/api": {
        target: apiProxyTarget,
        changeOrigin: true,
        rewrite: (proxyPath: string) => proxyPath.replace(/^\/api/, ""),
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
  },
});
