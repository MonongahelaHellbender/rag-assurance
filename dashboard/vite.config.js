import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// base './' makes the built site work at any path — including a GitHub Pages project subpath
// like username.github.io/<repo>/ — without hardcoding the repo name.
export default defineConfig({
  base: './',
  plugins: [react()],
})
