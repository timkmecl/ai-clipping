import tailwindcss from '@tailwindcss/vite';
import react from '@vitejs/plugin-react';
import path from 'path';
import {defineConfig, loadEnv} from 'vite';

export default defineConfig(({mode}) => {
  const env = loadEnv(mode, '.', '');
  return {
    base: '/ai-clipping/', // Set to your repo name
    plugins: [react(), tailwindcss()],
      define: {
        'process.env.API_URL': JSON.stringify(env.API_URL || 'http://localhost:4102/api')
      },
    resolve: {
      alias: {
        '@': path.resolve(__dirname, '.'),
      },
    },
    server: {
      hmr: process.env.DISABLE_HMR !== 'true',
    },
    build: {
      outDir: 'dist',
    },
  };
});
