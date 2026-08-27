import { useMemo } from "react";
import {
  BarChart,
  Bar,
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
import { useCharts } from "@/hooks/useDashboardData";
import type { ChartResponse, ChartDataPoint } from "@/types/api";

function BarChartCard({ chart }: { chart: ChartResponse }) {
  const data = useMemo(
    () => chart.data.map((d: ChartDataPoint) => ({ name: d.label, value: d.value })),
    [chart.data],
  );

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium">{chart.title}</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(217.2 32.6% 17.5%)" />
            <XAxis dataKey="name" tick={{ fill: "hsl(215 20.2% 65.1%)", fontSize: 12 }} />
            <YAxis tick={{ fill: "hsl(215 20.2% 65.1%)", fontSize: 12 }} />
            <Tooltip
              contentStyle={{
                backgroundColor: "hsl(222.2 84% 4.9%)",
                border: "1px solid hsl(217.2 32.6% 17.5%)",
                borderRadius: "8px",
                color: "hsl(210 40% 98%)",
              }}
            />
            <Bar dataKey="value" fill="hsl(217.2 91.2% 59.8%)" radius={[4, 4, 0, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

function FunnelChartCard({ chart }: { chart: ChartResponse }) {
  const data = useMemo(
    () => chart.data.map((d: ChartDataPoint) => ({ name: d.label, value: d.value })),
    [chart.data],
  );

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium">{chart.title}</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <BarChart data={data} layout="vertical">
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(217.2 32.6% 17.5%)" />
            <XAxis type="number" tick={{ fill: "hsl(215 20.2% 65.1%)", fontSize: 12 }} />
            <YAxis
              type="category"
              dataKey="name"
              tick={{ fill: "hsl(215 20.2% 65.1%)", fontSize: 12 }}
              width={140}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: "hsl(222.2 84% 4.9%)",
                border: "1px solid hsl(217.2 32.6% 17.5%)",
                borderRadius: "8px",
                color: "hsl(210 40% 98%)",
              }}
            />
            <Bar dataKey="value" fill="hsl(217.2 91.2% 59.8%)" radius={[0, 4, 4, 0]} />
          </BarChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

function LineChartCard({ chart }: { chart: ChartResponse }) {
  const data = useMemo(
    () => chart.data.map((d: ChartDataPoint) => ({ name: d.label, value: d.value })),
    [chart.data],
  );

  return (
    <Card>
      <CardHeader className="pb-2">
        <CardTitle className="text-sm font-medium">{chart.title}</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <LineChart data={data}>
            <CartesianGrid strokeDasharray="3 3" stroke="hsl(217.2 32.6% 17.5%)" />
            <XAxis dataKey="name" tick={{ fill: "hsl(215 20.2% 65.1%)", fontSize: 12 }} />
            <YAxis tick={{ fill: "hsl(215 20.2% 65.1%)", fontSize: 12 }} />
            <Tooltip
              contentStyle={{
                backgroundColor: "hsl(222.2 84% 4.9%)",
                border: "1px solid hsl(217.2 32.6% 17.5%)",
                borderRadius: "8px",
                color: "hsl(210 40% 98%)",
              }}
            />
            <Line
              type="monotone"
              dataKey="value"
              stroke="hsl(217.2 91.2% 59.8%)"
              strokeWidth={2}
              dot={{ fill: "hsl(217.2 91.2% 59.8%)", r: 4 }}
              activeDot={{ r: 6 }}
            />
          </LineChart>
        </ResponsiveContainer>
      </CardContent>
    </Card>
  );
}

function ChartCard({ chart }: { chart: ChartResponse }) {
  switch (chart.chart_type) {
    case "funnel":
      return <FunnelChartCard chart={chart} />;
    case "line":
      return <LineChartCard chart={chart} />;
    case "bar":
    default:
      return <BarChartCard chart={chart} />;
  }
}

export function ChartsGrid() {
  const { data: charts, isLoading, error } = useCharts();

  if (isLoading) {
    return (
      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        {Array.from({ length: 4 }).map((_, i) => (
          <Card key={i}>
            <CardContent className="flex h-[340px] items-center justify-center">
              <LoadingSpinner />
            </CardContent>
          </Card>
        ))}
      </div>
    );
  }

  if (error) {
    return (
      <div className="rounded-md border border-destructive/50 bg-destructive/10 p-4 text-sm text-destructive">
        Erro ao carregar gráficos: {error.message}
      </div>
    );
  }

  if (!charts?.length) return null;

  return (
    <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
      {charts.map((chart) => (
        <ChartCard key={chart.title} chart={chart} />
      ))}
    </div>
  );
}
