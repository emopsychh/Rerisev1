import { apiRequest } from "./client";
import { clearTokens, setTokens } from "./session";
import type { AuthUser, MeUser, TokenPair } from "./types";

export type AuthResponse = TokenPair & { user: AuthUser };

export async function login(email: string, password: string) {
  const data = await apiRequest<AuthResponse>("/auth/login", {
    method: "POST",
    auth: false,
    body: { email, password },
  });
  setTokens(data.access_token, data.refresh_token);
  return data;
}

export async function register(payload: {
  email: string;
  password: string;
  first_name?: string;
  last_name?: string;
  phone?: string;
  referral_code?: string;
}) {
  const data = await apiRequest<AuthResponse>("/auth/register", {
    method: "POST",
    auth: false,
    body: payload,
  });
  setTokens(data.access_token, data.refresh_token);
  return data;
}

export async function fetchMe() {
  return apiRequest<MeUser>("/me");
}

export function logout() {
  clearTokens();
}
