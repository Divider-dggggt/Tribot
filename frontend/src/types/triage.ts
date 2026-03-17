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
}
