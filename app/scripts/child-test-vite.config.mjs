// Isolated browser-test proxy. No requests reach the configured live database.
import {defineConfig} from 'vite';
export default defineConfig({
  resolve:{dedupe:['react','react-dom','react-router','react-router-dom']},
  server:{host:'127.0.0.1',port:5175,strictPort:true,proxy:{'/api':{target:'http://127.0.0.1:5501',changeOrigin:true}}},
});
