import { TrendingUp, DollarSign, BarChart3, CheckCircle } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import { useKPIs } from "@/hooks/useDashboardData";

const kpiConfig = [
  { title: "Total de Deals", icon: TrendingUp, format: (v: number) => v.toLocaleString("pt-BR") },
  { title: "Valor do Pipeline", icon: DollarSign, format: (v: number) => v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" }) },
  { title: "Ticket Médio", icon: BarChart3, format: (v: number) => v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" }) },
  { title: "Deals Fechados", icon: CheckCircle, format: (v: number) => v.toLocaleString("pt-BR") },
] as const;

export function KPICards() {
  const { data: kpis, isLoading, error } = useKPIs();

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 4 }).map((_, i) => (
          <Card key={i}>
            <CardContent className="flex h-28 items-center justify-center">
              <LoadingSpinner size="sm" />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-md border border-destructive/50 bg-destructive/10 p-4 text-sm text-destructive">
        Erro ao carregar KPIs: {error.message}
      </div>
    );
  }

  if (!kpis?.length) return null;

  return (
    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
      {kpis.map((kpi, i) => {
        const config = kpiConfig[i] ?? kpiConfig[0]!;
        const Icon = config.icon;
        return (
          <Card key={kpi.title}>
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {kpi.title}
              </CardTitle>
              <Icon className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{config.format(kpi.value)}</div>
            </CardContent>
          </Card>
        );
      })}
    </div>
  );
}
