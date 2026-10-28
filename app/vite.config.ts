import { defineConfig } from 'vite';

export default defineConfig({
  resolve: { dedupe: ['react', 'react-dom', 'react-router', 'react-router-dom'] },
  server: { proxy: { '/api': { target: 'http://127.0.0.1:5001', changeOrigin: true } } },
  preview: { proxy: { '/api': { target: 'http://127.0.0.1:5001', changeOrigin: true } } },
});
