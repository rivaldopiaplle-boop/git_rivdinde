import tailwindcss from '@tailwindcss/vite'
import vue from '@vitejs/plugin-vue'
// defineConfig vient de vitest/config et non de vite : c'est lui qui connait
// la cle `test`. Sans cela, vue-tsc refuse le fichier de configuration.
import { defineConfig } from 'vitest/config'

export default defineConfig({
  plugins: [vue(), tailwindcss()],
  server: {
    port: 5173,
    // Ecoute aussi sur l'adresse locale du reseau, pour ouvrir le front depuis
    // le navigateur d'un telephone sans rien reconfigurer.
    host: true,
  },
  test: {
    environment: 'jsdom',
    setupFiles: ['./src/tests-preparation.ts'],
    include: ['src/**/*.test.ts'],
  },
})
