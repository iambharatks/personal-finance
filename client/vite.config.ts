/// <reference types="vitest/config" />
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // Same origin as in production: the browser only ever talks to /api.
    proxy: { "/api": "http://127.0.0.1:8000" },
  },
  test: { environment: "node", include: ["src/**/*.test.ts"] },
});
