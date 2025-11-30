import { fileURLToPath, URL } from 'node:url';
import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import vueJsx from '@vitejs/plugin-vue-jsx';
import vueDevTools from 'vite-plugin-vue-devtools';

export default defineConfig(({ mode }) => {
  // 根据环境设置API基础URL
  const isProduction = mode === 'production';
  
  return {
    plugins: [vue(), vueJsx(), vueDevTools()],
    resolve: {
      alias: {
        '@': fileURLToPath(new URL('./src', import.meta.url)),
      },
    },
    base: isProduction ? '/admin/' : '/',
    define: {
      // 定义环境变量 - 本地测试环境使用代理避免跨域
      'import.meta.env.VITE_API_BASE_URL': JSON.stringify('/api'),
      'import.meta.env.VITE_DELIVERY_API_BASE_URL': JSON.stringify('/api'),
    },
    server: {
      port: 5173,
      // 重新启用代理来解决跨域问题
      proxy: {
        '/api': {
          target: 'http://localhost:8001',
          changeOrigin: true,
          rewrite: (path) => path.replace(/^\/api/, ''),
          configure: (proxy, options) => {
            proxy.on('error', (err, req, res) => {
              console.log('proxy error', err);
            });
            proxy.on('proxyReq', (proxyReq, req, res) => {
              console.log('Sending Request to the Target:', req.method, req.url);
            });
            proxy.on('proxyRes', (proxyRes, req, res) => {
              console.log('Received Response from the Target:', proxyRes.statusCode, req.url);
            });
          },
        }
      }
    }
  };
});