import { apiClient } from "./client";
import type {
  ProductResponse,
  ProductUpdate,
  OrderResponse,
  CustomerResponse,
  KPIResponse,
} from "@/types/api";

export async function fetchDashboardKPIs(): Promise<KPIResponse[]> {
  const { data } = await apiClient.get<KPIResponse[]>("/dashboard/kpis");
  return data;
}

export async function fetchProducts(
  page: number = 1,
  page_size: number = 20,
): Promise<ProductResponse[]> {
  const { data } = await apiClient.get<ProductResponse[]>("/dashboard/products", {
    params: { page, page_size },
  });
  return data;
}

export async function updateProduct(
  id: number,
  update: ProductUpdate,
): Promise<ProductResponse> {
  const { data } = await apiClient.patch<ProductResponse>(
    `/dashboard/products/${id}`,
    update,
  );
  return data;
}

export async function fetchOrders(
  page: number = 1,
  page_size: number = 20,
  status?: string,
): Promise<OrderResponse[]> {
  const params: Record<string, unknown> = { page, page_size };
  if (status) params.status = status;
  const { data } = await apiClient.get<OrderResponse[]>("/dashboard/orders", {
    params,
  });
  return data;
}

export async function fetchOrderDetail(id: number): Promise<OrderResponse> {
  const { data } = await apiClient.get<OrderResponse>(`/dashboard/orders/${id}`);
  return data;
}

export async function fetchCustomers(): Promise<CustomerResponse[]> {
  const { data } = await apiClient.get<CustomerResponse[]>("/dashboard/customers");
  return data;
}
