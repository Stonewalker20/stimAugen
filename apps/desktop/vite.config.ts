import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "node:path";
import { fileURLToPath } from "node:url";

const rootDir = fileURLToPath(new URL(".", import.meta.url));

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(rootDir, "./src"),
      "@tauri-apps/api/core": path.resolve(rootDir, "../../node_modules/@tauri-apps/api/core.js"),
    },
  },
  server: {
    port: 1420,
    strictPort: true,
  },
});
