import { useQuery } from "@tanstack/react-query";
import { fetchQuotes, fetchHistory } from "@/api/market";

export function useMarketQuotes(pairs: string = "USD-BRL,EUR-BRL") {
  return useQuery({
    queryKey: ["market", "quotes", pairs],
    queryFn: () => fetchQuotes(pairs),
    staleTime: 1 * 60 * 1000, // 1 minute
  });
}

export function useMarketHistory(moeda: string, dias: number = 30) {
  return useQuery({
    queryKey: ["market", "history", moeda, dias],
    queryFn: () => fetchHistory(moeda, dias),
    staleTime: 5 * 60 * 1000, // 5 minutes
  });
}
