from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.entities.product import Product


class ProductRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self, limit: int = 100, offset: int = 0) -> list[Product]:
        result = await self.session.execute(
            select(Product).order_by(Product.id).offset(offset).limit(limit)
        )
        return list(result.scalars().all())

    async def get_by_id(self, product_id: int) -> Product | None:
        result = await self.session.execute(
            select(Product).where(Product.id == product_id)
        )
        return result.scalar_one_or_none()

    async def update(self, product: Product, data: dict) -> Product:
        for key, value in data.items():
            if value is not None and hasattr(product, key):
                setattr(product, key, value)
        await self.session.flush()
        return product

    async def get_low_stock(self, threshold: int = 10) -> list[Product]:
        result = await self.session.execute(
            select(Product).where(Product.estoque < threshold, Product.ativo.is_(True))
        )
        return list(result.scalars().all())

    async def get_top_selling(self, limit: int = 5) -> list[dict]:
        from sqlalchemy import func

        from app.entities.order_item import OrderItem

        result = await self.session.execute(
            select(
                Product.id,
                Product.nome,
                Product.preco,
                func.sum(OrderItem.quantidade).label("total_vendido"),
            )
            .join(OrderItem, OrderItem.product_id == Product.id)
            .group_by(Product.id, Product.nome, Product.preco)
            .order_by(func.sum(OrderItem.quantidade).desc())
            .limit(limit)
        )
        return [
            {"id": r.id, "nome": r.nome, "preco": r.preco, "total_vendido": int(r.total_vendido or 0)}
            for r in result.all()
        ]
