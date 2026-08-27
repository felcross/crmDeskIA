import axios, { type AxiosError, type InternalAxiosRequestConfig } from "axios";
import type { ResponseEnvelope, ErrorResponse } from "@/types/api";

const apiClient = axios.create({
  baseURL: "/api/v1",
  headers: {
    "Content-Type": "application/json",
  },
});

function getCsrfToken(): string | null {
  const match = document.cookie.match(/(?:^|;\s*)csrf_token=([^;]*)/);
  return match?.[1] ?? null;
}

apiClient.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const token = getCsrfToken();
  if (token) {
    config.headers.set("X-CSRF-Token", token);
  }
  return config;
});

apiClient.interceptors.response.use(
  (response) => {
    const body = response.data as ResponseEnvelope<unknown>;
    if (body && typeof body === "object" && "data" in body) {
      response.data = body.data;
      if (body.meta) {
        (response as unknown as Record<string, unknown>).pagination = body.meta;
      }
    }
    return response;
  },
  (error: AxiosError<ErrorResponse>) => {
    if (error.response) {
      const errData = error.response.data;
      const message =
        errData?.error?.message ?? error.message ?? "Erro desconhecido";
      return Promise.reject(new Error(message));
    }
    return Promise.reject(error);
  },
);

export { apiClient };
