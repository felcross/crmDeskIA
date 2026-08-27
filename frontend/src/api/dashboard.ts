import { apiClient } from "./client";
import type {
  KPIResponse,
  ChartResponse,
  DealResponse,
  LeadResponse,
  PaginationParams,
  PaginatedResponse,
} from "@/types/api";

export async function fetchKPIs(): Promise<KPIResponse[]> {
  const { data } = await apiClient.get<KPIResponse[]>("/dashboard/kpis");
  return data;
}

export async function fetchCharts(): Promise<ChartResponse[]> {
  const { data } = await apiClient.get<ChartResponse[]>("/dashboard/charts");
  return data;
}

export async function fetchDeals(
  params?: PaginationParams,
): Promise<PaginatedResponse<DealResponse>> {
  const res = await apiClient.get<DealResponse[]>("/dashboard/deals", {
    params,
  });
  return {
    data: res.data,
    pagination: (res as unknown as Record<string, unknown>).pagination as PaginatedResponse<DealResponse>["pagination"],
  };
}

export async function fetchLeads(
  params?: PaginationParams,
): Promise<PaginatedResponse<LeadResponse>> {
  const res = await apiClient.get<LeadResponse[]>("/dashboard/leads", {
    params,
  });
  return {
    data: res.data,
    pagination: (res as unknown as Record<string, unknown>).pagination as PaginatedResponse<LeadResponse>["pagination"],
  };
}
