import { useState, useEffect, useCallback } from "react";

export interface CartItem {
  product_id: number;
  nome: string;
  preco: number;
  quantidade: number;
  imagem_url: string | null;
}

const CART_KEY = "ecommerce_cart";
const ABANDONED_KEY = "ecommerce_cart_abandoned";

function loadCart(): CartItem[] {
  try {
    const raw = localStorage.getItem(CART_KEY);
    return raw ? JSON.parse(raw) : [];
  } catch {
    return [];
  }
}

function saveCart(items: CartItem[]) {
  localStorage.setItem(CART_KEY, JSON.stringify(items));
}

export function useCart() {
  const [items, setItems] = useState<CartItem[]>(loadCart);

  useEffect(() => {
    saveCart(items);
  }, [items]);

  const addItem = useCallback((product: { id: number; nome: string; preco: number; imagem_url: string | null }) => {
    setItems((prev) => {
      const existing = prev.find((i) => i.product_id === product.id);
      if (existing) {
        return prev.map((i) =>
          i.product_id === product.id ? { ...i, quantidade: i.quantidade + 1 } : i,
        );
      }
      return [
        ...prev,
        {
          product_id: product.id,
          nome: product.nome,
          preco: product.preco,
          quantidade: 1,
          imagem_url: product.imagem_url,
        },
      ];
    });
  }, []);

  const removeItem = useCallback((productId: number) => {
    setItems((prev) => prev.filter((i) => i.product_id !== productId));
  }, []);

  const updateQuantity = useCallback((productId: number, quantidade: number) => {
    if (quantidade <= 0) {
      setItems((prev) => prev.filter((i) => i.product_id !== productId));
    } else {
      setItems((prev) =>
        prev.map((i) =>
          i.product_id === productId ? { ...i, quantidade } : i,
        ),
      );
    }
  }, []);

  const clearCart = useCallback(() => {
    setItems([]);
  }, []);

  const total = items.reduce((sum, i) => sum + i.preco * i.quantidade, 0);
  const itemCount = items.reduce((sum, i) => sum + i.quantidade, 0);

  const markAbandoned = useCallback(async (cliente_nome: string, cliente_email: string) => {
    if (items.length === 0) return;
    const abandoned = JSON.parse(localStorage.getItem(ABANDONED_KEY) || "[]");
    const key = `${cliente_email}-${Date.now()}`;
    if (abandoned.includes(key)) return;

    try {
      await fetch("/api/v1/ecommerce/orders/abandoned", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          cliente_nome,
          cliente_email,
          valor_total: total,
          itens: items.map((i) => ({ product_id: i.product_id, nome: i.nome, quantidade: i.quantidade })),
        }),
      });
      abandoned.push(key);
      localStorage.setItem(ABANDONED_KEY, JSON.stringify(abandoned));
    } catch {
      // Silent fail — abandoned cart tracking is best-effort
    }
  }, [items, total]);

  return { items, addItem, removeItem, updateQuantity, clearCart, total, itemCount, markAbandoned };
}
