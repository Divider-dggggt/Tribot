export enum UserRole {
  Admin = "Admin",
  Clinician = "Clinician",
  Researcher = "Researcher",
}

export interface User {
  name: string;
  email: string;
  role: UserRole;
  id: number;
  created_at: string;
}

export interface AccessTokenPayload {
  exp: number;
  user_id: number;
  role: UserRole;
}
