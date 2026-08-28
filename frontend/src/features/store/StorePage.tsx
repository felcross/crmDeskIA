import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { ShoppingCart, Plus, Minus, Trash2, ArrowLeft, Store } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import { useCart } from "./useCart";
import type { ProductResponse } from "@/types/api";

function formatCurrency(v: number) {
  return v.toLocaleString("pt-BR", { style: "currency", currency: "BRL" });
}

function ProductCard({
  product,
  onAdd,
}: {
  product: ProductResponse;
  onAdd: (p: ProductResponse) => void;
}) {
  const outOfStock = product.estoque <= 0;

  return (
    <Card className={outOfStock ? "opacity-50" : ""}>
      <CardContent className="p-4">
        <div className="mb-3 flex h-40 items-center justify-center rounded-md bg-muted">
          {product.imagem_url ? (
            <img src={product.imagem_url} alt={product.nome} className="h-full w-full rounded-md object-cover" />
          ) : (
            <Store className="h-12 w-12 text-muted-foreground" />
          )}
        </div>
        <h3 className="font-medium">{product.nome}</h3>
        <p className="mt-1 text-sm text-muted-foreground line-clamp-2">{product.descricao}</p>
        <div className="mt-3 flex items-center justify-between">
          <span className="text-lg font-bold">{formatCurrency(product.preco)}</span>
          {outOfStock ? (
            <span className="text-sm text-red-400">Indisponível</span>
          ) : (
            <Button size="sm" onClick={() => onAdd(product)}>
              <Plus className="mr-1 h-4 w-4" />
              Adicionar
            </Button>
          )}
        </div>
        {!outOfStock && product.estoque < 10 && (
          <p className="mt-1 text-xs text-yellow-400">Últimas {product.estoque} unidades</p>
        )}
      </CardContent>
    </Card>
  );
}

function CartSidebar({
  items,
  total,
  itemCount,
  onUpdate,
  onRemove,
  onCheckout,
  onClose,
}: {
  items: ReturnType<typeof useCart>["items"];
  total: number;
  itemCount: number;
  onUpdate: (id: number, qty: number) => void;
  onRemove: (id: number) => void;
  onCheckout: () => void;
  onClose: () => void;
}) {
  return (
    <div className="fixed inset-y-0 right-0 z-50 w-full max-w-md border-l bg-background shadow-lg">
      <div className="flex h-full flex-col">
        <div className="flex items-center justify-between border-b p-4">
          <h2 className="text-lg font-semibold">Carrinho ({itemCount})</h2>
          <Button variant="ghost" size="icon" onClick={onClose}>
            <Trash2 className="h-4 w-4" />
          </Button>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {items.length === 0 ? (
            <p className="text-center text-muted-foreground">Carrinho vazio</p>
          ) : (
            items.map((item) => (
              <div key={item.product_id} className="flex items-center gap-3 rounded-md border p-3">
                <div className="flex-1">
                  <p className="text-sm font-medium">{item.nome}</p>
                  <p className="text-sm text-muted-foreground">{formatCurrency(item.preco)}</p>
                </div>
                <div className="flex items-center gap-2">
                  <Button size="icon" variant="outline" className="h-7 w-7" onClick={() => onUpdate(item.product_id, item.quantidade - 1)}>
                    <Minus className="h-3 w-3" />
                  </Button>
                  <span className="w-6 text-center text-sm">{item.quantidade}</span>
                  <Button size="icon" variant="outline" className="h-7 w-7" onClick={() => onUpdate(item.product_id, item.quantidade + 1)}>
                    <Plus className="h-3 w-3" />
                  </Button>
                </div>
                <Button size="icon" variant="ghost" className="h-7 w-7 text-red-400" onClick={() => onRemove(item.product_id)}>
                  <Trash2 className="h-3 w-3" />
                </Button>
              </div>
            ))
          )}
        </div>

        {items.length > 0 && (
          <div className="border-t p-4 space-y-3">
            <div className="flex justify-between text-lg font-bold">
              <span>Total</span>
              <span>{formatCurrency(total)}</span>
            </div>
            <Button className="w-full" size="lg" onClick={onCheckout}>
              Finalizar Compra
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}

function CheckoutForm({
  total,
  onSubmit,
  onBack,
  isSubmitting,
}: {
  total: number;
  onSubmit: (nome: string, email: string) => void;
  onBack: () => void;
  isSubmitting: boolean;
}) {
  const [nome, setNome] = useState("");
  const [email, setEmail] = useState("");

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (nome.trim() && email.trim()) {
      onSubmit(nome.trim(), email.trim());
    }
  }

  return (
    <Card className="mx-auto max-w-md">
      <CardHeader>
        <CardTitle>Finalizar Compra</CardTitle>
      </CardHeader>
      <CardContent>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="nome">Nome completo</Label>
            <Input id="nome" value={nome} onChange={(e) => setNome(e.target.value)} required placeholder="Seu nome" />
          </div>
          <div className="space-y-2">
            <Label htmlFor="email">E-mail</Label>
            <Input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} required placeholder="seu@email.com" />
          </div>
          <div className="rounded-md bg-muted p-3 text-sm">
            <span className="text-muted-foreground">Total:</span>{" "}
            <span className="font-bold">{formatCurrency(total)}</span>
          </div>
          <div className="flex gap-2">
            <Button type="button" variant="outline" onClick={onBack}>
              <ArrowLeft className="mr-1 h-4 w-4" />
              Voltar
            </Button>
            <Button type="submit" className="flex-1" disabled={isSubmitting}>
              {isSubmitting ? "Processando..." : "Confirmar Pedido"}
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}

function OrderConfirmation({ orderId, qrUrl, onClose }: { orderId: number; qrUrl: string; onClose: () => void }) {
  return (
    <Card className="mx-auto max-w-md">
      <CardHeader>
        <CardTitle className="text-center text-emerald-400">Pedido Confirmado!</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4 text-center">
        <p className="text-muted-foreground">Seu pedido #{orderId} foi criado com sucesso.</p>
        <p className="text-sm text-muted-foreground">Um e-mail de confirmação foi enviado com o QR Code para pagamento.</p>
        <div className="flex justify-center">
          <img src={qrUrl} alt="QR Code" className="h-48 w-48" />
        </div>
        <p className="text-xs text-muted-foreground">Escaneie o QR Code para simular o pagamento</p>
        <Button className="w-full" onClick={onClose}>
          Voltar à Loja
        </Button>
      </CardContent>
    </Card>
  );
}

type View = "catalog" | "checkout" | "confirmation";

export default function StorePage() {
  const [products, setProducts] = useState<ProductResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [cartOpen, setCartOpen] = useState(false);
  const [view, setView] = useState<View>("catalog");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [orderResult, setOrderResult] = useState<{ id: number; qr_url: string } | null>(null);

  const cart = useCart();

  useEffect(() => {
    fetch("/api/v1/ecommerce/products?page_size=50")
      .then((r) => r.json())
      .then((body) => {
        setProducts(body.data ?? []);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, []);

  // Track abandoned cart on page unload
  useEffect(() => {
    function handleBeforeUnload() {
      if (cart.items.length > 0) {
        // Mark as abandoned (best-effort, uses navigator.sendBeacon pattern)
        const data = JSON.stringify({
          cliente_nome: "Visitante",
          cliente_email: "anonimo@loja.com",
          valor_total: cart.total,
          itens: cart.items.map((i) => ({ product_id: i.product_id, nome: i.nome, quantidade: i.quantidade })),
        });
        navigator.sendBeacon("/api/v1/ecommerce/orders/abandoned", new Blob([data], { type: "application/json" }));
      }
    }
    window.addEventListener("beforeunload", handleBeforeUnload);
    return () => window.removeEventListener("beforeunload", handleBeforeUnload);
  }, [cart.items, cart.total]);

  async function handleCheckout(nome: string, email: string) {
    setIsSubmitting(true);
    try {
      const resp = await fetch("/api/v1/ecommerce/orders", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          cliente_nome: nome,
          cliente_email: email,
          itens: cart.items.map((i) => ({ product_id: i.product_id, quantidade: i.quantidade })),
        }),
      });
      const body = await resp.json();
      if (resp.ok && body.data) {
        setOrderResult({ id: body.data.id, qr_url: body.data.qr_code_url });
        cart.clearCart();
        setView("confirmation");
        // Refresh products to update stock
        const prodResp = await fetch("/api/v1/ecommerce/products?page_size=50");
        const prodBody = await prodResp.json();
        setProducts(prodBody.data ?? []);
      } else {
        alert(body.detail || "Erro ao criar pedido");
      }
    } catch {
      alert("Erro de conexão. Tente novamente.");
    } finally {
      setIsSubmitting(false);
    }
  }

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center">
        <LoadingSpinner />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-40 border-b bg-background/95 backdrop-blur">
        <div className="mx-auto flex h-14 max-w-6xl items-center justify-between px-4">
          <Link to="/" className="flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground">
            <ArrowLeft className="h-4 w-4" />
            Voltar
          </Link>
          <h1 className="text-lg font-semibold">Loja de Beleza</h1>
          <Button variant="outline" size="sm" onClick={() => setCartOpen(true)} className="relative">
            <ShoppingCart className="h-4 w-4" />
            {cart.itemCount > 0 && (
              <span className="absolute -right-2 -top-2 flex h-5 w-5 items-center justify-center rounded-full bg-primary text-xs text-primary-foreground">
                {cart.itemCount}
              </span>
            )}
          </Button>
        </div>
      </header>

      {/* Content */}
      <main className="mx-auto max-w-6xl px-4 py-8">
        {view === "catalog" && (
          <>
            <h2 className="mb-6 text-2xl font-bold">Nossos Produtos</h2>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4">
              {products.map((p) => (
                <ProductCard key={p.id} product={p} onAdd={cart.addItem} />
              ))}
            </div>
          </>
        )}

        {view === "checkout" && (
          <CheckoutForm
            total={cart.total}
            onSubmit={handleCheckout}
            onBack={() => setView("catalog")}
            isSubmitting={isSubmitting}
          />
        )}

        {view === "confirmation" && orderResult && (
          <OrderConfirmation
            orderId={orderResult.id}
            qrUrl={orderResult.qr_url}
            onClose={() => {
              setView("catalog");
              setOrderResult(null);
            }}
          />
        )}
      </main>

      {/* Cart Sidebar */}
      {cartOpen && (
        <>
          <div className="fixed inset-0 z-40 bg-black/50" onClick={() => setCartOpen(false)} />
          <CartSidebar
            items={cart.items}
            total={cart.total}
            itemCount={cart.itemCount}
            onUpdate={cart.updateQuantity}
            onRemove={cart.removeItem}
            onCheckout={() => {
              setCartOpen(false);
              setView("checkout");
            }}
            onClose={() => setCartOpen(false)}
          />
        </>
      )}
    </div>
  );
}
