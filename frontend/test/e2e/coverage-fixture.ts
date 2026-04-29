import { randomUUID } from "node:crypto";
import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";
import { expect, test as base, type Page } from "@playwright/test";

type CoveragePayload = Record<string, unknown>;

const isE2ECoverageEnabled = process.env.E2E_COVERAGE === "1";

const sanitizeSegment = (value: string): string => {
  const trimmed = value.trim();
  if (!trimmed) {
    return "untitled";
  }
  return trimmed.replace(/[^a-zA-Z0-9_-]+/g, "_").slice(0, 120);
};

const readCoverageFromPage = async (page: Page): Promise<CoveragePayload | null> => {
  const coveragePayload = await page.evaluate(() => {
    const currentWindow = window as Window & { __coverage__?: unknown };
    return currentWindow.__coverage__ ?? null;
  }).catch(() => null);

  if (coveragePayload == null || typeof coveragePayload !== "object") {
    return null;
  }
  return coveragePayload as CoveragePayload;
};

export const test = base.extend({
  page: async ({ page }, use, testInfo) => {
    await use(page);

    if (!isE2ECoverageEnabled) {
      return;
    }

    const coveragePayload = await readCoverageFromPage(page);
    if (coveragePayload == null || Object.keys(coveragePayload).length === 0) {
      return;
    }

    const outputDirectory = path.resolve(process.cwd(), ".nyc_output");
    await mkdir(outputDirectory, { recursive: true });

    const testSlug = sanitizeSegment(testInfo.title);
    const outputName = `e2e-${testInfo.workerIndex}-${testSlug}-${Date.now()}-${randomUUID()}.json`;
    await writeFile(
      path.join(outputDirectory, outputName),
      JSON.stringify(coveragePayload),
      "utf8",
    );
  },
});

export { expect };
