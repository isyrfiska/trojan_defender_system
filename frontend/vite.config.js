import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: 'localhost',
    port: 3000,
    strictPort: true, // Force the specified port
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        secure: false,
      },
      '/ws': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        ws: true,
      }
    }
  },
  build: {
    outDir: 'dist',
    target: 'esnext',
    // Ensure proper handling of routes in production
    rollupOptions: {
      output: {
        manualChunks: undefined,
      },
    },
  },
  // Handle client-side routing in preview mode
  preview: {
    host: 'localhost',
    port: 3000
  },
  // Optimize dependencies and handle esbuild
  optimizeDeps: {
    esbuildOptions: {
      target: 'esnext'
    }
  }
})