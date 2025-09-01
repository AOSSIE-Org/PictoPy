import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react-swc';
import path from 'path';

// Vite config
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, 'src'),  // Maps `@` to `src` folder
      '@pages': path.resolve(__dirname, 'src/Pages'), // Maps `@pages` to `src/Pages` folder
    },
  },
});
