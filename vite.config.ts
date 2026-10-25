import { defineConfig } from "vite";
export default defineConfig({
  root: "frontend",
  build: { outDir: "../src/raid_handshake/static", emptyOutDir: true },
  server: {
    proxy: {
      "/api": "http://127.0.0.1:8765",
      "/ws": { target: "ws://127.0.0.1:8765", ws: true },
    },
  },
});
