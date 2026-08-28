import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import { useOrders, useOrderDetail } from "@/hooks/useEcommerceData";
import type { OrderResponse } from "@/types/api";

const STATUS_LABELS: Record<string, string> = {
  pendente: "Pendente",
  pago: "Pago",
  enviado: "Enviado",
  entregue: "Entregue",
  cancelado: "Cancelado",
};

const STATUS_COLORS: Record<string, string> = {
  pendente: "bg-yellow-500/20 text-yellow-400",
  pago: "bg-blue-500/20 text-blue-400",
  enviado: "bg-purple-500/20 text-purple-400",
  entregue: "bg-emerald-500/20 text-emerald-400",
  cancelado: "bg-red-500/20 text-red-400",
};

function formatCurrency(v: number) {
  return v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

function formatDate(s: string) {
  return new Date(s).toLocaleDateString("pt-BR");
}

function OrderDetail({ order }: { order: OrderResponse }) {
  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-lg">
          Pedido #{order.id} — {order.cliente_nome}
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div>
            <span className="text-muted-foreground">Cliente:</span>{" "}
            {order.cliente_nome} ({order.cliente_email})
          </div>
          <div>
            <span className="text-muted-foreground">Status:</span>{" "}
            <span className={`rounded px-2 py-0.5 text-xs ${STATUS_COLORS[order.status] || ""}`}>
              {STATUS_LABELS[order.status] || order.status}
            </span>
          </div>
          <div>
            <span className="text-muted-foreground">Total:</span>{" "}
            {formatCurrency(order.total)}
          </div>
          <div>
            <span className="text-muted-foreground">Data:</span>{" "}
            {formatDate(order.criado_em)}
          </div>
        </div>

        {order.qr_code_url && (
          <div>
            <span className="text-sm text-muted-foreground">QR Code:</span>
            <img src={order.qr_code_url} alt="QR Code" className="mt-1 h-32 w-32" />
          </div>
        )}

        <div>
          <h4 className="mb-2 text-sm font-medium">Itens</h4>
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-left text-muted-foreground">
                <th className="pb-2">Produto</th>
                <th className="pb-2">Qtd</th>
                <th className="pb-2">Preço Unit.</th>
                <th className="pb-2">Subtotal</th>
              </tr>
            </thead>
            <tbody>
              {order.itens.map((item) => (
                <tr key={item.id} className="border-b">
                  <td className="py-2">{item.product_nome}</td>
                  <td className="py-2">{item.quantidade}</td>
                  <td className="py-2">{formatCurrency(item.preco_unitario)}</td>
                  <td className="py-2">{formatCurrency(item.quantidade * item.preco_unitario)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </CardContent>
    </Card>
  );
}

export default function OrdersPage() {
  const [statusFilter, setStatusFilter] = useState<string | undefined>();
  const [selectedId, setSelectedId] = useState<number | null>(null);
  const { data: orders, isLoading } = useOrders(1, statusFilter);
  const { data: detail } = useOrderDetail(selectedId ?? 0);

  if (isLoading) {
    return (
      <div className="flex h-64 items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">Pedidos</h1>
        <p className="text-muted-foreground">Pedidos gerados no e-commerce.</p>
      </div>

      <div className="flex gap-2">
        {[undefined, "pendente", "pago", "entregue", "cancelado"].map((s) => (
          <Button
            key={s ?? "all"}
            variant={statusFilter === s ? "default" : "outline"}
            size="sm"
            onClick={() => setStatusFilter(s)}
          >
            {s ? STATUS_LABELS[s] : "Todos"}
          </Button>
        ))}
      </div>

      {selectedId && detail && <OrderDetail order={detail} />}

      <Card>
        <CardContent className="p-0">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-left text-muted-foreground">
                <th className="p-3">#</th>
                <th className="p-3">Cliente</th>
                <th className="p-3">Itens</th>
                <th className="p-3">Total</th>
                <th className="p-3">Status</th>
                <th className="p-3">Data</th>
              </tr>
            </thead>
            <tbody>
              {(orders ?? []).map((order) => (
                <tr
                  key={order.id}
                  className="cursor-pointer border-b hover:bg-muted/50"
                  onClick={() => setSelectedId(order.id)}
                >
                  <td className="p-3">{order.id}</td>
                  <td className="p-3">{order.cliente_nome}</td>
                  <td className="p-3">{order.itens.length}</td>
                  <td className="p-3">{formatCurrency(order.total)}</td>
                  <td className="p-3">
                    <span className={`rounded px-2 py-0.5 text-xs ${STATUS_COLORS[order.status] || ""}`}>
                      {STATUS_LABELS[order.status] || order.status}
                    </span>
                  </td>
                  <td className="p-3">{formatDate(order.criado_em)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
}
