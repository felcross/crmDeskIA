from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.entities.order import Order


class OrderRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(
        self, limit: int = 100, offset: int = 0, status: str | None = None
    ) -> list[Order]:
        query = select(Order).options(selectinload(Order.itens))
        if status:
            query = query.where(Order.status == status)
        query = query.order_by(Order.criado_em.desc()).offset(offset).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().unique().all())

    async def get_by_id(self, order_id: int) -> Order | None:
        result = await self.session.execute(
            select(Order)
            .options(selectinload(Order.itens))
            .where(Order.id == order_id)
        )
        return result.scalar_one_or_none()

    async def get_stats(self) -> dict:
        now = datetime.now(timezone.utc)
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        # Total orders
        total = await self.session.execute(select(func.count(Order.id)))
        total_orders = total.scalar() or 0

        # Open vs closed
        open_q = await self.session.execute(
            select(func.count(Order.id)).where(Order.status.in_(["pendente", "pago"]))
        )
        open_orders = open_q.scalar() or 0

        closed_q = await self.session.execute(
            select(func.count(Order.id)).where(Order.status == "entregue")
        )
        closed_orders = closed_q.scalar() or 0

        # Revenue total (entregue only)
        rev_total = await self.session.execute(
            select(func.coalesce(func.sum(Order.total), 0)).where(Order.status == "entregue")
        )
        revenue_total = float(rev_total.scalar() or 0)

        # Revenue this month
        rev_month = await self.session.execute(
            select(func.coalesce(func.sum(Order.total), 0)).where(
                Order.status == "entregue", Order.criado_em >= month_start
            )
        )
        revenue_month = float(rev_month.scalar() or 0)

        # Average ticket
        ticket_medio = revenue_total / closed_orders if closed_orders > 0 else 0.0

        return {
            "total_pedidos": total_orders,
            "pedidos_abertos": open_orders,
            "pedidos_fechados": closed_orders,
            "faturamento_total": revenue_total,
            "faturamento_mes": revenue_month,
            "ticket_medio": round(ticket_medio, 2),
        }

    async def get_unique_customers(self) -> list[dict]:
        result = await self.session.execute(
            select(
                Order.cliente_email,
                Order.cliente_nome,
                func.count(Order.id).label("total_pedidos"),
                func.sum(Order.total).label("total_gasto"),
            )
            .group_by(Order.cliente_email, Order.cliente_nome)
            .order_by(func.sum(Order.total).desc())
        )
        return [
            {
                "email": r.cliente_email,
                "nome": r.cliente_nome,
                "total_pedidos": r.total_pedidos,
                "total_gasto": float(r.total_gasto or 0),
            }
            for r in result.all()
        ]
