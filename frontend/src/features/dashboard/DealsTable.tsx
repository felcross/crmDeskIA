import { useRef, useState } from "react";
import { useVirtualizer } from "@tanstack/react-virtual";
import { ArrowUpDown, ChevronLeft, ChevronRight } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import { useDeals } from "@/hooks/useDashboardData";
import type { PaginationParams } from "@/types/api";

const STAGES = [
  "Todos",
  "Prospecção",
  "Qualificação",
  "Proposta",
  "Negociação",
  "Fechado Ganho",
  "Fechado Perdido",
];

function formatCurrency(value: number | undefined | null): string {
  return (value ?? 0).toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

function formatDate(iso: string | null | undefined): string {
  return iso ? new Date(iso).toLocaleDateString("pt-BR") : "—";
}

const columns = [
  { key: "nome" as const, label: "Nome" },
  { key: "valor" as const, label: "Valor" },
  { key: "estagio" as const, label: "Estágio" },
  { key: "pipeline" as const, label: "Pipeline" },
  { key: "data_close" as const, label: "Data Close" },
  { key: "criado_em" as const, label: "Criado em" },
] as const;

type SortKey = (typeof columns)[number]["key"];

export function DealsTable() {
  const [page, setPage] = useState(1);
  const [sortBy, setSortBy] = useState<SortKey>("criado_em");
  const [sortOrder, setSortOrder] = useState<"asc" | "desc">("desc");
  const [stageFilter, setStageFilter] = useState("Todos");

  const params: PaginationParams = {
    page,
    page_size: 20,
    sort_by: sortBy,
    sort_order: sortOrder,
    stage: stageFilter === "Todos" ? undefined : stageFilter,
  };

  const { data, isLoading, error } = useDeals(params);
  const deals = data?.data ?? [];
  const pagination = data?.pagination;

  const parentRef = useRef<HTMLDivElement>(null);

  const virtualizer = useVirtualizer({
    count: deals.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 48,
    overscan: 5,
  });

  function handleSort(key: SortKey) {
    if (sortBy === key) {
      setSortOrder((o) => (o === "asc" ? "desc" : "asc"));
    } else {
      setSortBy(key);
      setSortOrder("asc");
    }
    setPage(1);
  }

  function renderCell(key: SortKey, deal: (typeof deals)[number]) {
    switch (key) {
      case "valor":
        return formatCurrency(deal.valor);
      case "data_close":
        return deal.data_close ? formatDate(deal.data_close) : "—";
      case "criado_em":
        return formatDate(deal.criado_em);
      case "pipeline":
        return deal.pipeline ?? "—";
      default:
        return deal[key] ?? "—";
    }
  }

  if (isLoading) {
    return (
      <Card>
        <CardContent className="flex h-64 items-center justify-center">
          <LoadingSpinner />
        </CardContent>
      </Card>
    );
  }

  if (error) {
    return (
      <div className="rounded-md border border-destructive/50 bg-destructive/10 p-4 text-sm text-destructive">
        Erro ao carregar ofertas: {error.message}
      </div>
    );
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between space-y-0">
        <CardTitle className="text-lg">Ofertas</CardTitle>
        <select
          value={stageFilter}
          onChange={(e) => {
            setStageFilter(e.target.value);
            setPage(1);
          }}
          className="rounded-md border bg-background px-3 py-1.5 text-sm"
        >
          {STAGES.map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-left text-muted-foreground">
                {columns.map((col) => (
                  <th key={col.key} className="pb-3 pr-4">
                    <button
                      onClick={() => handleSort(col.key)}
                      className="inline-flex items-center gap-1 hover:text-foreground"
                    >
                      {col.label}
                      <ArrowUpDown className="h-3 w-3" />
                    </button>
                  </th>
                ))}
              </tr>
            </thead>
          </table>

          <div ref={parentRef} className="h-[400px] overflow-auto">
            <table className="w-full text-sm">
              <tbody>
                {virtualizer.getVirtualItems().map((virtualRow) => {
                  const deal = deals[virtualRow.index]!;
                  return (
                    <tr
                      key={deal.id}
                      className="border-b"
                      style={{
                        height: virtualRow.size,
                        transform: `translateY(${virtualRow.start - virtualizer.getVirtualItems()[0]!.start}px)`,
                      }}
                    >
                      {columns.map((col) => (
                        <td key={col.key} className="py-3 pr-4">
                          {renderCell(col.key, deal)}
                        </td>
                      ))}
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>

        {pagination && (
          <div className="mt-4 flex items-center justify-between text-sm text-muted-foreground">
            <span>
              Página {pagination.page} de {pagination.total_pages} ({pagination.total} itens)
            </span>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                disabled={page <= 1}
                onClick={() => setPage((p) => p - 1)}
              >
                <ChevronLeft className="h-4 w-4" />
              </Button>
              <Button
                variant="outline"
                size="sm"
                disabled={page >= pagination.total_pages}
                onClick={() => setPage((p) => p + 1)}
              >
                <ChevronRight className="h-4 w-4" />
              </Button>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
