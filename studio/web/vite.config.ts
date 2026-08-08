import react from "@vitejs/plugin-react";
// vitest/config re-exports Vite's defineConfig with the `test` block typed.
import { defineConfig } from "vitest/config";

// The FastAPI service the dev server proxies to. Production serves the built
// assets from the same origin, so no proxy is involved there.
const API_TARGET = process.env.STUDIO_API_URL ?? "http://127.0.0.1:8000";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    host: "127.0.0.1",
    proxy: {
      "/api": { target: API_TARGET, changeOrigin: true },
      "/health": { target: API_TARGET, changeOrigin: true },
      "/assets": { target: API_TARGET, changeOrigin: true },
      // The Social bench uses the generated V1-V3 assets directly. Proxying this
      // keeps development and the single-origin production build identical.
      "/social-assets": { target: API_TARGET, changeOrigin: true },
    },
  },
  build: {
    outDir: "dist",
    assetsDir: "static",
    sourcemap: true,
  },
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
    css: false,
  },
});
