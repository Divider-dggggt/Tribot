import { jwtDecode } from "jwt-decode";
import { AccessTokenPayload } from "../types/user";

export const isAuthenticated = (): boolean => Boolean(localStorage.getItem("access_token"));

export const getDecodedToken = (): AccessTokenPayload | null => {
  const token = localStorage.getItem("access_token");
  if (token == null) return null;
  return jwtDecode<AccessTokenPayload>(token);
};
