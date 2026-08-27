import { useQuery } from "@tanstack/react-query";
import {
  fetchKPIs,
  fetchCharts,
  fetchDeals,
  fetchLeads,
} from "@/api/dashboard";
import type { PaginationParams } from "@/types/api";

export function useKPIs() {
  return useQuery({
    queryKey: ["dashboard", "kpis"],
    queryFn: fetchKPIs,
    staleTime: 5 * 60 * 1000,
  });
}

export function useCharts() {
  return useQuery({
    queryKey: ["dashboard", "charts"],
    queryFn: fetchCharts,
  });
}

export function useDeals(params?: PaginationParams) {
  return useQuery({
    queryKey: ["dashboard", "deals", params],
    queryFn: () => fetchDeals(params),
    placeholderData: (prev) => prev,
  });
}

export function useLeads(params?: PaginationParams) {
  return useQuery({
    queryKey: ["dashboard", "leads", params],
    queryFn: () => fetchLeads(params),
    placeholderData: (prev) => prev,
  });
}
