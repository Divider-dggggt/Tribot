export interface DashboardCaseObject {
  case_id: number;
  user_id: number;
  patient_name: string;
  medicare_number: string;
  severity_flagged: boolean;
  resolved_at: string | null;
  created_at: string;
  ats_category: number;
  ats_source: string;
  override_ats?: number | null;
  override_reason?: string | null;
  age?: number | null;
  gender?: string | null;
}

export interface SeverityFlag {
  flag_category: number;
  flag_reason: string;
}

export interface CaseObject {
    case_id: number;
    patient_name: string;
    medicare_number: string;
    case_dialogue: string;
    severity_flagged: boolean;
    resolved_at: string | null;
    created_at: string;
    soap_summary: string;
    brief_summary: string;
    ats_category: number;
    ats_source: string;
    override_ats?: number | null;
    override_reason?: string | null;
    age?: number | null;
    gender?: string | null;
    pred_ats: number;
    pred_confidence: number;
    model_used: string;
    flag_ats?: number | null;
    flag_notes?: string | null;
}
