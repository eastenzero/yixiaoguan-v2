import { defineConfig } from "vite";
import uni from "@dcloudio/vite-plugin-uni";

export default defineConfig({
  plugins: [uni()],
  server: {
    port: 3000,
    host: true,
    proxy: {
      '/api': {
        target: 'https://yxg.xiaoguan.site',
        changeOrigin: true
      },
      '/ws': {
        target: 'wss://yxg.xiaoguan.site',
        ws: true,
        changeOrigin: true
      }
    }
  }
});
