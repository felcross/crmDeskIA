import type {
  CurrencyQuote,
  CurrencyQuoteResponse,
  CurrencyHistoryResponse,
} from "@/types/api";

export async function fetchQuotes(
  pairs: string = "USD-BRL,EUR-BRL",
): Promise<CurrencyQuoteResponse> {
  const res = await fetch(
    `/api/v1/market/quotes?pairs=${encodeURIComponent(pairs)}`,
  );
  if (!res.ok) return { quotes: [] };
  const raw = await res.json();

  // AwesomeAPI raw format: {"USDBRL": {...}, "EURBRL": {...}}
  if (raw && typeof raw === "object" && !Array.isArray(raw) && !("quotes" in raw) && !("data" in raw)) {
    const quotes: CurrencyQuote[] = Object.values(raw).filter(
      (v): v is Record<string, unknown> =>
        typeof v === "object" && v !== null && "bid" in v,
    ).map((v) => ({
      code: String(v.code ?? ""),
      codein: String(v.codein ?? ""),
      name: String(v.name ?? ""),
      bid: Number(v.bid ?? 0),
      ask: Number(v.ask ?? 0),
      varBid: Number(v.varBid ?? 0),
      pctChange: Number(v.pctChange ?? 0),
      high: Number(v.high ?? 0),
      low: Number(v.low ?? 0),
      timestamp: Number(v.timestamp ?? 0),
    }));
    return { quotes };
  }

  // Wrapped format (from backend fallback)
  const body = (raw as Record<string, unknown>)?.data ?? raw;
  return (body as CurrencyQuoteResponse)?.quotes
    ? (body as CurrencyQuoteResponse)
    : { quotes: [] };
}

export async function fetchHistory(
  moeda: string,
  dias: number = 30,
): Promise<CurrencyHistoryResponse> {
  const res = await fetch(
    `/api/v1/market/history/${encodeURIComponent(moeda)}?dias=${dias}`,
  );
  if (!res.ok) return { moeda, dias, data: [] };
  const raw = await res.json();

  // AwesomeAPI raw format: [{timestamp, bid, ask}, ...]
  if (Array.isArray(raw)) {
    return {
      moeda,
      dias,
      data: raw.map((p) => ({
        timestamp: Number(p.timestamp ?? 0),
        bid: Number(p.bid ?? 0),
        ask: Number(p.ask ?? 0),
      })),
    };
  }

  // Wrapped format (from backend fallback)
  const body = (raw as Record<string, unknown>)?.data ?? raw;
  return (body as CurrencyHistoryResponse)?.data
    ? (body as CurrencyHistoryResponse)
    : { moeda, dias, data: [] };
}
