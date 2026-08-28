import { TrendingUp, DollarSign, BarChart3, CheckCircle, Info } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { useKPIs } from "@/hooks/useDashboardData";

const kpiConfig = [
  { title: "Total de Ofertas", icon: TrendingUp, format: (v: number) => v.toLocaleString("pt-BR"), tooltip: "Quantidade total de oportunidades de venda em andamento" },
  { title: "Valor do Pipeline", icon: DollarSign, format: (v: number) => v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" }), tooltip: "Soma do valor de todas as ofertas em aberto — quanto a empresa pode faturar se todas fecharem" },
  { title: "Ticket Médio", icon: BarChart3, format: (v: number) => v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" }), tooltip: "Valor médio por oferta fechada" },
  { title: "Ofertas Fechadas", icon: CheckCircle, format: (v: number) => v.toLocaleString("pt-BR"), tooltip: "Quantidade de ofertas que já viraram venda" },
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
              <CardTitle className="flex items-center gap-1.5 text-sm font-medium text-muted-foreground">
                {kpi.title}
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button className="text-muted-foreground/60 hover:text-muted-foreground transition-colors">
                      <Info className="h-3.5 w-3.5" />
                    </button>
                  </TooltipTrigger>
                  <TooltipContent side="top" className="max-w-xs">
                    {config.tooltip}
                  </TooltipContent>
                </Tooltip>
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
