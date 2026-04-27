import { expect, test } from "@playwright/test";
import { mockEmptyCases, signInAs } from "./helpers";

const CREATED_CASE_ID = 4242;

test("a clinician can create a case and land on the triage result", async ({ page }) => {
  await signInAs(page, "clinician");
  await mockEmptyCases(page);

  await page.route("http://localhost:8000/triage", async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        case_id: CREATED_CASE_ID,
        severity_flagged: false,
        soap_summary: "Subjective: chest pain",
        ats_classification: 3,
        confidence_score: 0.82,
        flagged_keywords: null,
      }),
    });
  });

  await page.route(`http://localhost:8000/cases/${CREATED_CASE_ID}`, async (route) => {
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        case_id: CREATED_CASE_ID,
        patient_name: "John Doe",
        medicare_number: "12345678901",
        case_dialogue: "Severe chest pain",
        severity_flagged: false,
        resolved_at: null,
        created_at: "2026-04-25T10:00:00Z",
        soap_summary: "Subjective: chest pain\n\nObjective: normal vitals\n\nAssessment: angina\n\nPlan: ECG",
        brief_summary: "Chest pain",
        ats_category: 3,
        ats_source: "model",
        pred_ats: 3,
        pred_confidence: 0.82,
        model_used: "test-model",
      }),
    });
  });

  await page.goto("/new-case");

  await page.getByLabel(/medicare card number/i).fill("1234567890/1");
  await page.getByLabel(/patient name/i).fill("John Doe");
  await page.getByLabel(/case details/i).fill("Severe chest pain");

  await page.getByRole("button", { name: /submit for triage/i }).click();

  await expect(page).toHaveURL(new RegExp(`\\?case=${CREATED_CASE_ID}$`));
  await expect(page.getByRole("heading", { name: "Triage Result" })).toBeVisible();
  await expect(page.getByText("John Doe")).toBeVisible();
});
