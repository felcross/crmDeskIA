"""Seed script — popula o banco do e-commerce com dados mockados.

Uso: docker compose run --rm ecommerce-backend python scripts/seed.py
"""
import asyncio
import json
import random
from datetime import datetime, timedelta, timezone

from app.db.session import async_session, engine
from app.entities import AbandonedCart, Base, EmailLog, Order, OrderItem, Product
from sqlalchemy import text

PRODUCTS = [
    {"nome": "Batom Matte Ruby", "descricao": "Batom de longa duração, acabamento matte", "preco": 49.90, "estoque": 200, "imagem_url": "https://placehold.co/300x300?text=Batom"},
    {"nome": "Base Fluida HD", "descricao": "Base de cobertura média a alta, 30ml", "preco": 89.90, "estoque": 120, "imagem_url": "https://placehold.co/300x300?text=Base"},
    {"nome": "Sérum Vitamina C", "descricao": "Sérum antioxidante anti-idade, 30ml", "preco": 129.90, "estoque": 75, "imagem_url": "https://placehold.co/300x300?text=Serum"},
    {"nome": "Protetor Solar FPS 50", "descricao": "Protetor solar facial oil-free, 50g", "preco": 69.90, "estoque": 180, "imagem_url": "https://placehold.co/300x300?text=Protetor"},
    {"nome": "Máscara de Cílios Volume", "descricao": "Máscara para volume e alongamento", "preco": 59.90, "estoque": 90, "imagem_url": "https://placehold.co/300x300?text=Mascara"},
    {"nome": "Hidratante Corporal Vanilla", "descricao": "Creme hidratante corporal 400ml", "preco": 39.90, "estoque": 6, "imagem_url": "https://placehold.co/300x300?text=Hidratante"},
    {"nome": "Paleta de Sombras 12 Cores", "descricao": "Paleta com tons neutros e vibrantes", "preco": 119.90, "estoque": 50, "imagem_url": "https://placehold.co/300x300?text=Paleta"},
    {"nome": "Shampoo Reparação", "descricao": "Shampoo para cabelos danificados, 300ml", "preco": 34.90, "estoque": 4, "imagem_url": "https://placehold.co/300x300?text=Shampoo"},
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

QR_BASE = "https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=PEDIDO-"


async def seed():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with async_session() as session:
        # Check if already seeded
        result = await session.execute(text("SELECT COUNT(*) FROM products"))
        if result.scalar() > 0:
            print("Banco já populado — seed ignorado.")
            return

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

        # Insert abandoned carts
        abandoned_data = [
            {"email": "maria@email.com", "nome": "Maria Santos", "valor": 189.80, "itens": [{"product_id": 1, "nome": "Batom Matte Ruby", "qty": 2}, {"product_id": 4, "nome": "Protetor Solar FPS 50", "qty": 1}]},
            {"email": "pedro@email.com", "nome": "Pedro Oliveira", "valor": 129.90, "itens": [{"product_id": 3, "nome": "Sérum Vitamina C", "qty": 1}]},
            {"email": "ana@email.com", "nome": "Ana Costa", "valor": 259.70, "itens": [{"product_id": 7, "nome": "Paleta de Sombras", "qty": 1}, {"product_id": 5, "nome": "Máscara de Cílios", "qty": 1}, {"product_id": 1, "nome": "Batom Matte Ruby", "qty": 1}]},
            {"email": "lucas@email.com", "nome": "Lucas Pereira", "valor": 69.90, "itens": [{"product_id": 4, "nome": "Protetor Solar FPS 50", "qty": 1}]},
            {"email": "juliana@email.com", "nome": "Juliana Lima", "valor": 315.00, "itens": [{"product_id": 3, "nome": "Sérum Vitamina C", "qty": 1}, {"product_id": 7, "nome": "Paleta de Sombras", "qty": 1}, {"product_id": 2, "nome": "Base Fluida HD", "qty": 1}]},
        ]
        for ac in abandoned_data:
            cart = AbandonedCart(
                cliente_email=ac["email"],
                cliente_nome=ac["nome"],
                valor_total=ac["valor"],
                itens_json=json.dumps(ac["itens"], ensure_ascii=False),
                criado_em=now - timedelta(days=random.randint(1, 10)),
            )
            session.add(cart)

        # Insert email logs
        email_data = [
            {"para": "joao@email.com", "assunto": "Pedido #1 confirmado — QR Code para pagamento", "tipo": "confirmacao"},
            {"para": "maria@email.com", "assunto": "Seu pedido #2 foi enviado!", "tipo": "envio"},
            {"para": "pedro@email.com", "assunto": "Pedido #3 entregue com sucesso", "tipo": "entrega"},
            {"para": "ana@email.com", "assunto": "Você esqueceu algo no carrinho!", "tipo": "carrinho"},
            {"para": "lucas@email.com", "assunto": "Pedido #5 confirmado — QR Code para pagamento", "tipo": "confirmacao"},
            {"para": "juliana@email.com", "assunto": "Promoção especial: 15% off em séruns", "tipo": "promocao"},
            {"para": "carlos@email.com", "assunto": "Pedido #7 enviado — acompanhe sua entrega", "tipo": "envio"},
            {"para": "beatriz@email.com", "assunto": "Pedido #8 entregue! Avalie sua experiência", "tipo": "entrega"},
            {"para": "marcos@email.com", "assunto": "Carrinho abandonado — ganhe 10% off", "tipo": "carrinho"},
            {"para": "fernanda@email.com", "assunto": "Pedido #10 confirmado — QR Code para pagamento", "tipo": "confirmacao"},
        ]
        for i, em in enumerate(email_data):
            email_log = EmailLog(
                para=em["para"],
                assunto=em["assunto"],
                tipo=em["tipo"],
                enviado_em=now - timedelta(days=random.randint(0, 15)),
            )
            session.add(email_log)

        await session.commit()
        print(f"  {len(order_objs)} pedidos criados com itens")
        print(f"  {len(abandoned_data)} carrinhos abandonados criados")
        print(f"  {len(email_data)} e-mails fake registrados")
        print("Seed concluído!")


if __name__ == "__main__":
    asyncio.run(seed())
