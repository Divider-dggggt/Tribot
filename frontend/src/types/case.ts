export interface DashboardCaseObject {
  case_id: number;
  user_id: number;
  name: string;
  medicare_number: string;
  case_details: string;
  severity_flagged: boolean;
  resolved_at: string | null;
  created_at: string;
  ats_classification: number;
  confidence_score: number;
  clinician_override_at: string | null;
}

export interface SeverityFlag {
  flag_category: number;
  flag_reason: string;
}

export interface CaseObject {
    case_id: number;
    user_id: number;
    name: string;
    medicare_number: string;
    case_details: string;
    severity_flagged: boolean;
    resolved_at: string | null;
    created_at: string;
    soap_summary: string;
    ats_classification: number;
    confidence_score: number;
    clinician_override_at: string | null;
    severity_flags: SeverityFlag[];
}
