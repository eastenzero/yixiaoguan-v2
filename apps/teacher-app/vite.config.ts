import { defineConfig } from "vite";
import uni from "@dcloudio/vite-plugin-uni";

export default defineConfig({
  plugins: [uni()],
  server: {
    port: 5300,
    host: true,
    proxy: {
      '/api': {
        target: 'https://teacher.xiaoguan.site',
        changeOrigin: true,
      },
      '/ws': {
        target: 'wss://teacher.xiaoguan.site',
        ws: true,
        changeOrigin: true,
      },
    }
  }
});
