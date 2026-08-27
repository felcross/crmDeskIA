import { useState } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import { useMarketQuotes, useMarketHistory } from "@/hooks/useMarketData";
import type { CurrencyQuote, HistoryPoint } from "@/types/api";

function formatBRL(value: number): string {
  return new Intl.NumberFormat("pt-BR", {
    style: "currency",
    currency: "BRL",
  }).format(value);
}

function formatDate(timestamp: number): string {
  return new Date(timestamp * 1000).toLocaleDateString("pt-BR", {
    day: "2-digit",
    month: "2-digit",
  });
}

function QuoteCard({ quote }: { quote: CurrencyQuote }) {
  const isPositive = quote.pctChange >= 0;

  return (
    <Card>
      <CardHeader className="pb-1">
        <CardTitle className="text-sm font-medium text-muted-foreground">
          {quote.code}/{quote.codein}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="text-2xl font-bold">{formatBRL(quote.bid)}</div>
        <div
          className={`text-sm font-medium ${isPositive ? "text-emerald-500" : "text-red-500"}`}
        >
          {isPositive ? "+" : ""}
          {quote.pctChange.toFixed(2)}%
        </div>
        <div className="mt-1 text-xs text-muted-foreground">
          Máx: {formatBRL(quote.high)} · Mín: {formatBRL(quote.low)}
        </div>
      </CardContent>
    </Card>
  );
}

function HistoryChart({
  moeda,
  dias,
}: {
  moeda: string;
  dias: number;
}) {
  const { data, isLoading, error } = useMarketHistory(moeda, dias);

  if (isLoading) {
    return (
      <div className="flex h-[250px] items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  if (error || !data?.data?.length) {
    return (
      <div className="flex h-[250px] items-center justify-center text-sm text-muted-foreground">
        Sem dados disponíveis
      </div>
    );
  }

  const chartData = data.data
    .slice()
    .reverse()
    .map((p: HistoryPoint) => ({
      date: formatDate(p.timestamp),
      bid: p.bid,
    }));

  return (
    <ResponsiveContainer width="100%" height={250}>
      <LineChart data={chartData}>
        <CartesianGrid strokeDasharray="3 3" stroke="hsl(217.2 32.6% 17.5%)" />
        <XAxis
          dataKey="date"
          tick={{ fill: "hsl(215 20.2% 65.1%)", fontSize: 11 }}
        />
        <YAxis
          tick={{ fill: "hsl(215 20.2% 65.1%)", fontSize: 11 }}
          domain={["auto", "auto"]}
          tickFormatter={(v: number) => v.toFixed(2)}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: "hsl(222.2 84% 4.9%)",
            border: "1px solid hsl(217.2 32.6% 17.5%)",
            borderRadius: "8px",
            color: "hsl(210 40% 98%)",
          }}
          formatter={(value) => [formatBRL(Number(value)), "Cotação"]}
        />
        <Line
          type="monotone"
          dataKey="bid"
          stroke="hsl(217.2 91.2% 59.8%)"
          strokeWidth={2}
          dot={false}
          activeDot={{ r: 4 }}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}

export function MarketWidget() {
  const [dias, setDias] = useState<15 | 30>(30);
  const { data, isLoading, error } = useMarketQuotes();

  if (isLoading) {
    return (
      <Card>
        <CardContent className="flex h-[200px] items-center justify-center">
          <LoadingSpinner />
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <Card>
        <CardContent className="flex h-[200px] items-center justify-center text-sm text-muted-foreground">
          Erro ao carregar cotações
        </CardContent>
      </Card>
    );
  }

  const quotes = data?.quotes ?? [];

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {quotes.map((quote) => (
          <QuoteCard key={`${quote.code}-${quote.codein}`} quote={quote} />
        ))}
      </div>

      <Card>
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <CardTitle className="text-sm font-medium">Histórico</CardTitle>
          <div className="flex gap-1">
            <button
              onClick={() => setDias(15)}
              className={`rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
                dias === 15
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted text-muted-foreground hover:bg-muted/80"
              }`}
            >
              15 dias
            </button>
            <button
              onClick={() => setDias(30)}
              className={`rounded-md px-2.5 py-1 text-xs font-medium transition-colors ${
                dias === 30
                  ? "bg-primary text-primary-foreground"
                  : "bg-muted text-muted-foreground hover:bg-muted/80"
              }`}
            >
              30 dias
            </button>
          </div>
        </CardHeader>
        <CardContent>
          {quotes[0] && (
            <HistoryChart moeda={`${quotes[0].code}-${quotes[0].codein}`} dias={dias} />
          )}
        </CardContent>
      </Card>
    </div>
  );
}
