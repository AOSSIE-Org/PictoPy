// vite.config.ts
import { defineConfig } from "file:///A:/PROFESSIONAL/PROGRAMMING/GSOC/AOSSIE/Parag-PictoPy/frontend/node_modules/vite/dist/node/index.js";
import react from "file:///A:/PROFESSIONAL/PROGRAMMING/GSOC/AOSSIE/Parag-PictoPy/frontend/node_modules/@vitejs/plugin-react/dist/index.mjs";
import path from "path";
import eslint from "file:///A:/PROFESSIONAL/PROGRAMMING/GSOC/AOSSIE/Parag-PictoPy/frontend/node_modules/vite-plugin-eslint/dist/index.mjs";
var __vite_injected_original_dirname = "A:\\PROFESSIONAL\\PROGRAMMING\\GSOC\\AOSSIE\\Parag-PictoPy\\frontend";
var vite_config_default = defineConfig(async () => ({
  plugins: [react(), eslint()],
  resolve: {
    alias: {
      "@": path.resolve(__vite_injected_original_dirname, "./src")
    }
  },
  // Vite options tailored for Tauri development and only applied in `tauri dev` or `tauri build`
  //
  // 1. prevent vite from obscuring rust errors
  clearScreen: false,
  // 2. tauri expects a fixed port, fail if that port is not available
  server: {
    port: 1420,
    strictPort: true,
    watch: {
      // 3. tell vite to ignore watching `src-tauri`
      ignored: ["**/src-tauri/**"]
    }
  }
}));
export {
  vite_config_default as default
};
//# sourceMappingURL=data:application/json;base64,ewogICJ2ZXJzaW9uIjogMywKICAic291cmNlcyI6IFsidml0ZS5jb25maWcudHMiXSwKICAic291cmNlc0NvbnRlbnQiOiBbImNvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9kaXJuYW1lID0gXCJBOlxcXFxQUk9GRVNTSU9OQUxcXFxcUFJPR1JBTU1JTkdcXFxcR1NPQ1xcXFxBT1NTSUVcXFxcUGFyYWctUGljdG9QeVxcXFxmcm9udGVuZFwiO2NvbnN0IF9fdml0ZV9pbmplY3RlZF9vcmlnaW5hbF9maWxlbmFtZSA9IFwiQTpcXFxcUFJPRkVTU0lPTkFMXFxcXFBST0dSQU1NSU5HXFxcXEdTT0NcXFxcQU9TU0lFXFxcXFBhcmFnLVBpY3RvUHlcXFxcZnJvbnRlbmRcXFxcdml0ZS5jb25maWcudHNcIjtjb25zdCBfX3ZpdGVfaW5qZWN0ZWRfb3JpZ2luYWxfaW1wb3J0X21ldGFfdXJsID0gXCJmaWxlOi8vL0E6L1BST0ZFU1NJT05BTC9QUk9HUkFNTUlORy9HU09DL0FPU1NJRS9QYXJhZy1QaWN0b1B5L2Zyb250ZW5kL3ZpdGUuY29uZmlnLnRzXCI7aW1wb3J0IHsgZGVmaW5lQ29uZmlnIH0gZnJvbSAndml0ZSc7XHJcbmltcG9ydCByZWFjdCBmcm9tICdAdml0ZWpzL3BsdWdpbi1yZWFjdCc7XHJcbmltcG9ydCBwYXRoIGZyb20gJ3BhdGgnO1xyXG5pbXBvcnQgZXNsaW50IGZyb20gJ3ZpdGUtcGx1Z2luLWVzbGludCc7XHJcblxyXG4vLyBodHRwczovL3ZpdGVqcy5kZXYvY29uZmlnL1xyXG5leHBvcnQgZGVmYXVsdCBkZWZpbmVDb25maWcoYXN5bmMgKCkgPT4gKHtcclxuICBwbHVnaW5zOiBbcmVhY3QoKSwgZXNsaW50KCldLFxyXG5cclxuICByZXNvbHZlOiB7XHJcbiAgICBhbGlhczoge1xyXG4gICAgICAnQCc6IHBhdGgucmVzb2x2ZShfX2Rpcm5hbWUsICcuL3NyYycpLFxyXG4gICAgfSxcclxuICB9LFxyXG4gIC8vIFZpdGUgb3B0aW9ucyB0YWlsb3JlZCBmb3IgVGF1cmkgZGV2ZWxvcG1lbnQgYW5kIG9ubHkgYXBwbGllZCBpbiBgdGF1cmkgZGV2YCBvciBgdGF1cmkgYnVpbGRgXHJcbiAgLy9cclxuICAvLyAxLiBwcmV2ZW50IHZpdGUgZnJvbSBvYnNjdXJpbmcgcnVzdCBlcnJvcnNcclxuICBjbGVhclNjcmVlbjogZmFsc2UsXHJcbiAgLy8gMi4gdGF1cmkgZXhwZWN0cyBhIGZpeGVkIHBvcnQsIGZhaWwgaWYgdGhhdCBwb3J0IGlzIG5vdCBhdmFpbGFibGVcclxuICBzZXJ2ZXI6IHtcclxuICAgIHBvcnQ6IDE0MjAsXHJcbiAgICBzdHJpY3RQb3J0OiB0cnVlLFxyXG4gICAgd2F0Y2g6IHtcclxuICAgICAgLy8gMy4gdGVsbCB2aXRlIHRvIGlnbm9yZSB3YXRjaGluZyBgc3JjLXRhdXJpYFxyXG4gICAgICBpZ25vcmVkOiBbJyoqL3NyYy10YXVyaS8qKiddLFxyXG4gICAgfSxcclxuICB9LFxyXG59KSk7XHJcbiJdLAogICJtYXBwaW5ncyI6ICI7QUFBMFgsU0FBUyxvQkFBb0I7QUFDdlosT0FBTyxXQUFXO0FBQ2xCLE9BQU8sVUFBVTtBQUNqQixPQUFPLFlBQVk7QUFIbkIsSUFBTSxtQ0FBbUM7QUFNekMsSUFBTyxzQkFBUSxhQUFhLGFBQWE7QUFBQSxFQUN2QyxTQUFTLENBQUMsTUFBTSxHQUFHLE9BQU8sQ0FBQztBQUFBLEVBRTNCLFNBQVM7QUFBQSxJQUNQLE9BQU87QUFBQSxNQUNMLEtBQUssS0FBSyxRQUFRLGtDQUFXLE9BQU87QUFBQSxJQUN0QztBQUFBLEVBQ0Y7QUFBQTtBQUFBO0FBQUE7QUFBQSxFQUlBLGFBQWE7QUFBQTtBQUFBLEVBRWIsUUFBUTtBQUFBLElBQ04sTUFBTTtBQUFBLElBQ04sWUFBWTtBQUFBLElBQ1osT0FBTztBQUFBO0FBQUEsTUFFTCxTQUFTLENBQUMsaUJBQWlCO0FBQUEsSUFDN0I7QUFBQSxFQUNGO0FBQ0YsRUFBRTsiLAogICJuYW1lcyI6IFtdCn0K
