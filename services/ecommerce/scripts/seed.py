"""Seed script — popula o banco do e-commerce com dados mockados.

Uso: docker compose run --rm ecommerce-backend python scripts/seed.py
"""
import asyncio
import random
from datetime import datetime, timedelta, timezone

from app.db.session import async_session, engine
from app.entities import Base, Order, OrderItem, Product
from sqlalchemy import text

PRODUCTS = [
    {"nome": "Camiseta Básica Algodão", "descricao": "Camiseta 100% algodão, várias cores", "preco": 79.90, "estoque": 150, "imagem_url": "https://placehold.co/300x300?text=Camiseta"},
    {"nome": "Calça Jeans Slim", "descricao": "Calça jeans masculina slim fit", "preco": 189.90, "estoque": 80, "imagem_url": "https://placehold.co/300x300?text=Calca"},
    {"nome": "Tênis Esportivo Runner", "descricao": "Tênis para corrida e caminhada", "preco": 299.90, "estoque": 45, "imagem_url": "https://placehold.co/300x300?text=Tenis"},
    {"nome": "Mochila Urban Pro", "descricao": "Mochila resistente para uso diário", "preco": 149.90, "estoque": 60, "imagem_url": "https://placehold.co/300x300?text=Mochila"},
    {"nome": "Boné Aba Reta", "descricao": "Boné estilo snapback", "preco": 59.90, "estoque": 200, "imagem_url": "https://placehold.co/300x300?text=Bone"},
    {"nome": "Jaqueta Corta-Vento", "descricao": "Jaqueta leve impermeável", "preco": 249.90, "estoque": 8, "imagem_url": "https://placehold.co/300x300?text=Jaqueta"},
    {"nome": "Meia Esportiva 3 pares", "descricao": "Kit com 3 pares de meias esportivas", "preco": 39.90, "estoque": 300, "imagem_url": "https://placehold.co/300x300?text=Meia"},
    {"nome": "Bolsa Tote Canvas", "descricao": "Bolsa de alça em canvas estampado", "preco": 119.90, "estoque": 5, "imagem_url": "https://placehold.co/300x300?text=Bolsa"},
]

CUSTOMERS = [
    {"nome": "João Silva", "email": "joao@email.com"},
    {"nome": "Maria Santos", "email": "maria@email.com"},
    {"nome": "Pedro Oliveira", "email": "pedro@email.com"},
    {"nome": "Ana Costa", "email": "ana@email.com"},
    {"nome": "Lucas Pereira", "email": "lucas@email.com"},
    {"nome": "Juliana Lima", "email": "juliana@email.com"},
    {"nome": "Carlos Souza", "email": "carlos@email.com"},
    {"nome": "Beatriz Almeida", "email": "beatriz@email.com"},
    {"nome": "Marcos Ribeiro", "email": "marcos@email.com"},
    {"nome": "Fernanda Martins", "email": "fernanda@email.com"},
]

STATUSES = ["pendente", "pago", "enviado", "entregue", "cancelado"]
QR_BASE = "https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=PEDIDO-"


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        # Check if already seeded
        result = await session.execute(text("SELECT COUNT(*) FROM products"))
        if result.scalar() > 0:
            print("Banco já populado. Limpando e re-seeding...")
            await session.execute(text("DELETE FROM order_items"))
            await session.execute(text("DELETE FROM orders"))
            await session.execute(text("DELETE FROM products"))
            await session.commit()

        # Insert products
        product_objs = []
        for p in PRODUCTS:
            product = Product(**p)
            session.add(product)
            product_objs.append(product)
        await session.flush()
        print(f"  {len(product_objs)} produtos criados")

        # Insert orders
        now = datetime.now(timezone.utc)
        order_objs = []
        for i in range(15):
            customer = CUSTOMERS[i % len(CUSTOMERS)]
            days_ago = random.randint(0, 30)
            order_date = now - timedelta(days=days_ago)

            # Distribute statuses: 8 entregue, 4 pendente/pago, 3 cancelado
            if i < 8:
                status = "entregue"
            elif i < 12:
                status = random.choice(["pendente", "pago"])
            else:
                status = "cancelado"

            order = Order(
                cliente_email=customer["email"],
                cliente_nome=customer["nome"],
                status=status,
                total=0.0,
                qr_code_url=f"{QR_BASE}{i+1}" if status in ("pago", "enviado", "entregue") else None,
                criado_em=order_date,
                atualizado_em=order_date + timedelta(hours=random.randint(1, 48)),
            )
            session.add(order)
            order_objs.append(order)
        await session.flush()

        # Insert order items
        for order in order_objs:
            num_items = random.randint(1, 4)
            chosen = random.sample(product_objs, min(num_items, len(product_objs)))
            total = 0.0
            for product in chosen:
                qty = random.randint(1, 3)
                item = OrderItem(
                    order_id=order.id,
                    product_id=product.id,
                    quantidade=qty,
                    preco_unitario=product.preco,
                )
                session.add(item)
                total += qty * product.preco
            order.total = round(total, 2)
        await session.flush()

        await session.commit()
        print(f"  {len(order_objs)} pedidos criados com itens")
        print("Seed concluído!")


if __name__ == "__main__":
    asyncio.run(seed())
