export enum ATSLevel {
  "ATS-1",
  "ATS-2",
  "ATS-3",
  "ATS-4",
  "ATS-5",
};

export interface TriageCase {
  id: string;
  name: string;
  date: string;
  priority: ATSLevel;
  confidence: number;
  details: string;
  caseId: number;
  safetyOverride?: boolean;
  flaggedKeywords: string | null;
  soapSummary: string;
}

export interface TriageApiResponse {
  case_id: number;
  severity_flagged: boolean;
  soap_summary: string;
  ats_classification: number;
  confidence_score: number;
  flagged_keywords: string | null;
}
