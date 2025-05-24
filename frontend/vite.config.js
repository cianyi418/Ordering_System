import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig({
  plugins: [vue()],
  server: {
    proxy: {
      "/test-uid": "http://localhost:8080",
      "/menu": "http://localhost:8080",
      "/get-orders": "http://localhost:8080",
      "/order": "http://localhost:8080",
      "/user-info": "http://localhost:8080",
      "/get-user": "http://localhost:8080",
      "/update-payment": "http://localhost:8080",
      "/update-shipping": "http://localhost:8080",
      "/shipping-rules": "http://localhost:8080",
    },
    historyApiFallback: true,
  },
  build: {
    outDir: "dist",
  },
});
