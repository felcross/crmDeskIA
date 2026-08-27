import { apiClient } from "./client";

export interface AuthUser {
  id: number;
  email: string;
  name: string;
  role: string;
  avatar_url: string | null;
}

export async function fetchMe(): Promise<AuthUser> {
  const { data } = await apiClient.get("/auth/me");
  return data;
}

export async function getGoogleLoginUrl(): Promise<string> {
  const { data } = await apiClient.get("/auth/login");
  if (data.url) {
    return data.url;
  }
  throw new Error(data.message ?? "Google OAuth is not configured.");
}

export async function logout(): Promise<void> {
  await apiClient.post("/auth/logout");
}
