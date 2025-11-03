import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 3000,
    watch: {
      usePolling: true
    },
    allowedHosts: [
      'machine-systems.org',   // Add your domain here
      'www.machine-systems.org'
    ]
  },
  preview: {
    host: '0.0.0.0',
    port: 3000
  }
})
