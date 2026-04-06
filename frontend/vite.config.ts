import { readFileSync } from "node:fs";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";

const appVersion = readFileSync(new URL("../VERSION", import.meta.url), "utf-8").trim();

export default defineConfig({
  define: {
    __APP_VERSION__: JSON.stringify(appVersion),
  },
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 5173,
  },
});
