import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': '/src'
    }
  },
  server: {
    port: 18505,
    proxy: {
      '/api': {
        target: 'http://localhost:19505',
        changeOrigin: true
      }
    }
  }
});
