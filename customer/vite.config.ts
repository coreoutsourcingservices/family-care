import { defineConfig } from 'vite';
import { fileURLToPath } from 'node:url';

export default defineConfig({
  resolve: { dedupe: ['react', 'react-dom', 'react-router', 'react-router-dom'] },
  publicDir: fileURLToPath(new URL('../app/public', import.meta.url)),
  server: { proxy: { '/api': { target: 'http://127.0.0.1:5001', changeOrigin: true } } },
  preview: { proxy: { '/api': { target: 'http://127.0.0.1:5001', changeOrigin: true } } },
});
