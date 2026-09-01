import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        // 127.0.0.1, not localhost: on Windows, Node resolves localhost to ::1
        // first, and uvicorn bound to 127.0.0.1 never answers there.
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})
