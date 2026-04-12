import { ATSLevel } from "../types/triage";

export const getPriorityColor = (priority: ATSLevel) => {
  switch (priority) {
    case ATSLevel['ATS-1']: return { bg: '#fee2e2', color: '#dc2626' };
    case ATSLevel['ATS-2']: return { bg: '#ffedd5', color: '#ea580c' };
    case ATSLevel['ATS-3']: return { bg: '#fef3c7', color: '#d97706' };
    case ATSLevel['ATS-4']: return { bg: '#dcfce7', color: '#16a34a' };
    case ATSLevel['ATS-5']: return { bg: '#dbeafe', color: '#2563eb' };
    default: return { bg: '#f3f4f6', color: '#374151' };
  }
};
