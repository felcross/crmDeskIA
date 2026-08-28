import structlog
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.entities.abandoned_cart import AbandonedCart
from app.entities.email_log import EmailLog
from app.models.common import ResponseEnvelope
from app.repositories.order_repo import OrderRepository
from app.repositories.product_repo import ProductRepository

log = structlog.get_logger()
router = APIRouter(prefix="/internal", tags=["internal"])


@router.get("/stats")
async def get_stats(db: AsyncSession = Depends(get_db)):  # noqa: B008
    repo = OrderRepository(db)
    stats = await repo.get_stats()
    return ResponseEnvelope(data=stats)


@router.get("/products/low-stock")
async def get_low_stock(db: AsyncSession = Depends(get_db)):  # noqa: B008
    repo = ProductRepository(db)
    products = await repo.get_low_stock(threshold=10)
    return ResponseEnvelope(
        data=[
            {"id": p.id, "nome": p.nome, "estoque": p.estoque, "preco": p.preco}
            for p in products
        ]
    )


@router.get("/products/top")
async def get_top_products(db: AsyncSession = Depends(get_db)):  # noqa: B008
    repo = ProductRepository(db)
    top = await repo.get_top_selling(limit=5)
    return ResponseEnvelope(data=top)


@router.get("/carts/abandoned")
async def get_abandoned_carts(db: AsyncSession = Depends(get_db)):  # noqa: B008
    """Return real abandoned carts from database."""
    result = await db.execute(
        select(AbandonedCart).order_by(AbandonedCart.criado_em.desc()).limit(50)
    )
    carts = result.scalars().all()
    return ResponseEnvelope(
        data=[
            {
                "cliente_email": c.cliente_email,
                "cliente_nome": c.cliente_nome,
                "valor": c.valor_total,
                "itens": c.itens_json,
                "abandonado_em": str(c.criado_em),
            }
            for c in carts
        ]
    )


@router.get("/emails")
async def get_email_history(db: AsyncSession = Depends(get_db)):  # noqa: B008
    """Return real email logs from database."""
    result = await db.execute(
        select(EmailLog).order_by(EmailLog.enviado_em.desc()).limit(50)
    )
    emails = result.scalars().all()
    return ResponseEnvelope(
        data=[
            {
                "para": e.para,
                "assunto": e.assunto,
                "tipo": e.tipo,
                "enviado_em": str(e.enviado_em),
            }
            for e in emails
        ]
    )
