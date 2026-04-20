export enum UserRole {
  Admin = "admin",
  Clinician = "clinician",
  Researcher = "researcher",
}

export interface User {
  name: string;
  email: string;
  role: UserRole;
  id: number;
  created_at: string;
  deactivated_at?: string | null;
}

export interface AccessTokenPayload {
  exp: number;
  user_id: number;
  role: UserRole;
}
