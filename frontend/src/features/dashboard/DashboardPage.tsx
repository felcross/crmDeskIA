import { KPICards } from "./KPICards";
import { ChartsGrid } from "./ChartsGrid";
import { MarketWidget } from "./MarketWidget";

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">
          Visão geral do negócio — vendas, pedidos e estoque.
        </p>
      </div>

      <KPICards />
      <ChartsGrid />
      <MarketWidget />
    </div>
  );
}
