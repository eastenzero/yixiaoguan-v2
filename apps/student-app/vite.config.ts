import { defineConfig } from "vite";
import uni from "@dcloudio/vite-plugin-uni";

export default defineConfig({
  plugins: [uni()],
  server: {
    port: 5174,
    host: true,
    proxy: {
      '/api': {
        target: 'http://192.168.100.165:8100',
        changeOrigin: true
      },
      '/ws': {
        target: 'ws://192.168.100.165:8100',
        ws: true,
        changeOrigin: true
      }
    }
  }
});
