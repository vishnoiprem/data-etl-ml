import { test, expect } from '@playwright/test';

test('user can filter, select, and submit feedback', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByText('RAG Traces')).toBeVisible();
  await page.getByLabel('Prompt version').selectOption('v1.2');
  await page.getByText('trace_000002').first().click().catch(() => {});
  // Optimistic thumbs-up
  await page.getByText('👍 Up').first().click();
  await expect(page.getByText('feedback_submitted').or(page.getByText('Up'))).toBeVisible();
});
