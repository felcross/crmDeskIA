import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { KPICards } from "./KPICards";
import { ChartsGrid } from "./ChartsGrid";
import { MarketWidget } from "./MarketWidget";
import { DealsTable } from "./DealsTable";

export default function DashboardPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Dashboard</h1>
        <p className="text-muted-foreground">
          Visão geral do seu CRM e pipeline de vendas.
        </p>
      </div>

      <Tabs defaultValue="overview">
        <TabsList>
          <TabsTrigger value="overview">Visão Geral</TabsTrigger>
          <TabsTrigger value="market">Cotações</TabsTrigger>
          <TabsTrigger value="data">Dados</TabsTrigger>
        </TabsList>

        <TabsContent value="overview" className="space-y-6">
          <KPICards />
          <ChartsGrid />
        </TabsContent>

        <TabsContent value="market" className="space-y-6">
          <MarketWidget />
        </TabsContent>

        <TabsContent value="data" className="space-y-6">
          <DealsTable />
        </TabsContent>
      </Tabs>
    </div>
  );
}
