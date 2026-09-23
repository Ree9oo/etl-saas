import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// 开发态将 /api 代理到后端（默认 8000 端口）
export default defineConfig({
  plugins: [vue()],
  base: '/',
  server: {
    host: '0.0.0.0',
    port: 5173,
    proxy: {
      '/api': {
        target: process.env.VITE_API_TARGET || 'http://localhost:8000',
        changeOrigin: true
      }
    }
  },
  build: {
    outDir: 'dist'
  }
})
