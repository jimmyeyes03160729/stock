// vite.config.ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  // ⚠️ 關鍵設定：如果是部署到 https://jimmyeyes03160729.github.io/stock/
  // 這裡必須設定為 '/stock/'
  base: '/stock/', 
})
