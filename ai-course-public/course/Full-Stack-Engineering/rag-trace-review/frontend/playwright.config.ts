import { defineConfig } from '@playwright/test';
export default defineConfig({
  testDir: './e2e',
  use: { baseURL: 'http://localhost:5173' },
  webServer: [
    { command: 'cd ../backend && uvicorn app.main:app --port 8000', port: 8000 },
    { command: 'npm run dev', port: 5173 },
  ],
});
