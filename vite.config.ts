TypeScript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  // 特別設定：對應倉庫名稱 /stock/，防止打包後 CSS/JS 404
  base: '/stock/',
});
