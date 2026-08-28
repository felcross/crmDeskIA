import {
  DollarSign,
  TrendingUp,
  ShoppingCart,
  CheckCircle,
  BarChart3,
  Package,
  AlertTriangle,
  Info,
} from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { useDashboardKPIs } from "@/hooks/useEcommerceData";

const kpiConfig: Record<string, { icon: typeof DollarSign; format: (v: number) => string; tooltip: string }> = {
  "Faturamento Total": {
    icon: DollarSign,
    format: (v) => v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" }),
    tooltip: "Receita total de pedidos entregues",
  },
  "Faturamento Mês": {
    icon: TrendingUp,
    format: (v) => v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" }),
    tooltip: "Receita do mês atual (pedidos entregues)",
  },
  "Pedidos Abertos": {
    icon: ShoppingCart,
    format: (v) => v.toLocaleString("pt-BR"),
    tooltip: "Pedidos pendentes ou pagos, aguardando processamento",
  },
  "Pedidos Fechados": {
    icon: CheckCircle,
    format: (v) => v.toLocaleString("pt-BR"),
    tooltip: "Pedidos entregues com sucesso",
  },
  "Ticket Médio": {
    icon: BarChart3,
    format: (v) => v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" }),
    tooltip: "Valor médio por pedido entregue",
  },
  "Estoque Baixo": {
    icon: Package,
    format: (v) => v.toLocaleString("pt-BR"),
    tooltip: "Produtos com menos de 10 unidades em estoque",
  },
  "Carrinhos Abandonados": {
    icon: AlertTriangle,
    format: (v) => v.toLocaleString("pt-BR"),
    tooltip: "Carrinhos que não viraram pedido",
  },
};

export function KPICards() {
  const { data: kpis, isLoading, error } = useDashboardKPIs();

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        {Array.from({ length: 7 }).map((_, i) => (
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
      {kpis.map((kpi) => {
        const config = kpiConfig[kpi.title] ?? {
          icon: BarChart3,
          format: (v: number) => v.toLocaleString("pt-BR"),
          tooltip: kpi.title,
        };
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
