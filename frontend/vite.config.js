import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 3000,
    watch: {
      usePolling: true,
    },
    allowedHosts: [
      'machine-systems.org', // Add your domain here
      'www.machine-systems.org',
    ],
    resolve: {
      dedupe: ['react', 'react-dom'],
    },
    fs: {
      // Override default deny list which blocks .env files and causes
      // noisy warnings in the Docker dev server logs. The dev server
      // is not publicly accessible, and no .env file exists in the
      // frontend container.
      deny: ['*.{crt,pem}'],
    },
  },
  preview: {
    host: '0.0.0.0',
    port: 3000,
  },
})
