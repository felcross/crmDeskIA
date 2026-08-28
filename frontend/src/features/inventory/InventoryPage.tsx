import { useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import { useProducts, useUpdateProduct } from "@/hooks/useEcommerceData";
import type { ProductResponse } from "@/types/api";

function formatCurrency(v: number) {
  return v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

function EditDialog({
  product,
  onClose,
}: {
  product: ProductResponse;
  onClose: () => void;
}) {
  const mutation = useUpdateProduct();
  const [nome, setNome] = useState(product.nome);
  const [preco, setPreco] = useState(String(product.preco));
  const [estoque, setEstoque] = useState(String(product.estoque));

  function handleSave() {
    mutation.mutate(
      {
        id: product.id,
        data: {
          nome,
          preco: parseFloat(preco),
          estoque: parseInt(estoque, 10),
        },
      },
      { onSuccess: onClose },
    );
  }

  return (
    <Card className="border-primary">
      <CardHeader>
        <CardTitle className="text-lg">Editar Produto #{product.id}</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-2">
          <Label>Nome</Label>
          <Input value={nome} onChange={(e) => setNome(e.target.value)} />
        </div>
        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label>Preço (R$)</Label>
            <Input type="number" step="0.01" value={preco} onChange={(e) => setPreco(e.target.value)} />
          </div>
          <div className="space-y-2">
            <Label>Estoque</Label>
            <Input type="number" value={estoque} onChange={(e) => setEstoque(e.target.value)} />
          </div>
        </div>
        <div className="flex gap-2">
          <Button onClick={handleSave} disabled={mutation.isPending}>
            {mutation.isPending ? "Salvando..." : "Salvar"}
          </Button>
          <Button variant="outline" onClick={onClose}>
            Cancelar
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}

export default function InventoryPage() {
  const { data: products, isLoading } = useProducts();
  const [editing, setEditing] = useState<ProductResponse | null>(null);

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
        <h1 className="text-2xl font-bold tracking-tight">Estoque</h1>
        <p className="text-muted-foreground">Gerencie os produtos do e-commerce.</p>
      </div>

      {editing && (
        <EditDialog product={editing} onClose={() => setEditing(null)} />
      )}

      <Card>
        <CardContent className="p-0">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b text-left text-muted-foreground">
                <th className="p-3">ID</th>
                <th className="p-3">Nome</th>
                <th className="p-3">Preço</th>
                <th className="p-3">Estoque</th>
                <th className="p-3">Status</th>
                <th className="p-3">Ação</th>
              </tr>
            </thead>
            <tbody>
              {(products ?? []).map((p) => (
                <tr key={p.id} className="border-b">
                  <td className="p-3">{p.id}</td>
                  <td className="p-3">{p.nome}</td>
                  <td className="p-3">{formatCurrency(p.preco)}</td>
                  <td className="p-3">
                    <span className={p.estoque < 10 ? "font-bold text-red-400" : ""}>
                      {p.estoque}
                    </span>
                  </td>
                  <td className="p-3">
                    {p.estoque < 10 ? (
                      <span className="rounded bg-red-500/20 px-2 py-0.5 text-xs text-red-400">
                        Baixo
                      </span>
                    ) : (
                      <span className="rounded bg-emerald-500/20 px-2 py-0.5 text-xs text-emerald-400">
                        OK
                      </span>
                    )}
                  </td>
                  <td className="p-3">
                    <Button size="sm" variant="outline" onClick={() => setEditing(p)}>
                      Editar
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </CardContent>
      </Card>
    </div>
  );
}
