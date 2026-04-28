import { UserRole } from "../types/user";

const envApiBaseUrl = import.meta.env.VITE_API_BASE_URL?.trim();

export const API_BASE_URL = (envApiBaseUrl && envApiBaseUrl.length > 0
  ? envApiBaseUrl
  : "http://localhost:8000").replace(/\/+$/, "");

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
