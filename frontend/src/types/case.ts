export interface CaseApiResponse {
  case_id: number;
  case_details: string;
  severity_flagged: boolean;
  resolved_at: string | null;
  created_at: string;
}
