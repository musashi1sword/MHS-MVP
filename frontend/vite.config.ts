import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The dev server proxies /api and /ws to the Django backend so the app runs
// from a single origin during the demo.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // Hosts the dev server will answer to. Vite rejects requests with an
    // unrecognised Host header by default, which blocked the domain in prod.
    allowedHosts: ["mwafrikahealth.com", "www.mwafrikahealth.com", "2.29.22.111"],
    host: "0.0.0.0",
    proxy: {
      "/api": { target: "http://localhost:8000", changeOrigin: true },
      "/ws": { target: "ws://localhost:8000", ws: true },
    },
  },
});
