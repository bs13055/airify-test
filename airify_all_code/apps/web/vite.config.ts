import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig(({ mode }) => ({
  plugins: [react()],
  // Keep local / FastAPI builds at root; use /Airify/ for GitHub Pages only.
  base: mode === 'github-pages' ? '/Airify/' : '/',
  server: {
    port: 5173,
    proxy: {
      '/v1': 'http://localhost:8000',
      '/healthz': 'http://localhost:8000',
      '/version': 'http://localhost:8000',
    },
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
}));
