import { apiClient } from "./client";
import type {
  CurrencyQuoteResponse,
  CurrencyHistoryResponse,
} from "@/types/api";

export async function fetchQuotes(
  pairs: string = "USD-BRL,EUR-BRL",
): Promise<CurrencyQuoteResponse> {
  const { data } = await apiClient.get<CurrencyQuoteResponse>("/market/quotes", {
    params: { pairs },
  });
  return data;
}

export async function fetchHistory(
  moeda: string,
  dias: number = 30,
): Promise<CurrencyHistoryResponse> {
  const { data } = await apiClient.get<CurrencyHistoryResponse>(
    `/market/history/${moeda}`,
    { params: { dias } },
  );
  return data;
}
