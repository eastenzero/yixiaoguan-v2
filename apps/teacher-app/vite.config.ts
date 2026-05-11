import { defineConfig } from "vite";
import uni from "@dcloudio/vite-plugin-uni";

export default defineConfig({
  plugins: [uni()],
  server: {
    port: 5300,
    host: true,
    proxy: {
      '/api': {
        target: 'http://192.168.100.165:8100',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://192.168.100.165:8100',
        ws: true,
        changeOrigin: true,
      },
      '/centrifugo': {
        target: 'http://127.0.0.1:18000',
        ws: true,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/centrifugo/, ''),
      },
    }
  }
});
