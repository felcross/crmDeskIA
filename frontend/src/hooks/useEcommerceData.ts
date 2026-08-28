import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  fetchDashboardKPIs,
  fetchProducts,
  updateProduct,
  fetchOrders,
  fetchOrderDetail,
  fetchCustomers,
} from "@/api/ecommerce";
import type { ProductUpdate } from "@/types/api";

export function useDashboardKPIs() {
  return useQuery({
    queryKey: ["dashboard", "kpis"],
    queryFn: fetchDashboardKPIs,
    staleTime: 2 * 60 * 1000,
  });
}

export function useProducts(page: number = 1) {
  return useQuery({
    queryKey: ["ecommerce", "products", page],
    queryFn: () => fetchProducts(page),
    staleTime: 1 * 60 * 1000,
  });
}

export function useUpdateProduct() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: number; data: ProductUpdate }) =>
      updateProduct(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["ecommerce", "products"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard", "kpis"] });
    },
  });
}

export function useOrders(page: number = 1, status?: string) {
  return useQuery({
    queryKey: ["ecommerce", "orders", page, status],
    queryFn: () => fetchOrders(page, 20, status),
    staleTime: 1 * 60 * 1000,
  });
}

export function useOrderDetail(id: number) {
  return useQuery({
    queryKey: ["ecommerce", "orders", id],
    queryFn: () => fetchOrderDetail(id),
    enabled: !!id,
  });
}

export function useCustomers() {
  return useQuery({
    queryKey: ["ecommerce", "customers"],
    queryFn: fetchCustomers,
    staleTime: 2 * 60 * 1000,
  });
}
