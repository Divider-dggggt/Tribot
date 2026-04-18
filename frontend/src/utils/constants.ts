import { UserRole } from "../types/user";

export const API_BASE_URL = "http://localhost:8000";

export const ROLE_PERMISSIONS: Record<UserRole, string[]> = {
  [UserRole.Admin]: [
    "View all patient records",
    "Access evaluation tools",
    "Generate reports",
    "Administrative access",
  ],
  [UserRole.Clinician]: [
    "Create new cases",
    "Override AI predictions",
    "Access evaluation tools",
  ],
  [UserRole.Researcher]: [
    "Generate reports",
    "View all patient records",
    "Access evaluation tools",
  ],
};
