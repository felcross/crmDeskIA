import structlog
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
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
async def get_abandoned_carts():
    """Mock: carrinhos abandonados (dados de seed)."""
    return ResponseEnvelope(
        data=[
            {"cliente_email": "maria@email.com", "valor": 450.00, "itens": 3, "abandonado_em": "2026-08-25T14:30:00"},
            {"cliente_email": "pedro@email.com", "valor": 189.90, "itens": 1, "abandonado_em": "2026-08-26T09:15:00"},
            {"cliente_email": "ana@email.com", "valor": 720.50, "itens": 5, "abandonado_em": "2026-08-27T16:45:00"},
            {"cliente_email": "lucas@email.com", "valor": 99.90, "itens": 1, "abandonado_em": "2026-08-27T20:10:00"},
            {"cliente_email": "juliana@email.com", "valor": 315.00, "itens": 2, "abandonado_em": "2026-08-28T08:00:00"},
        ]
    )


@router.get("/emails")
async def get_email_history():
    """Mock: histórico de e-mails fake enviados."""
    return ResponseEnvelope(
        data=[
            {"para": "joao@email.com", "assunto": "Pedido #1 confirmado", "tipo": "confirmacao", "enviado_em": "2026-08-20T10:00:00"},
            {"para": "maria@email.com", "assunto": "Seu pedido #2 foi enviado", "tipo": "envio", "enviado_em": "2026-08-21T14:30:00"},
            {"para": "pedro@email.com", "assunto": "Pedido #3 entregue", "tipo": "entrega", "enviado_em": "2026-08-22T09:00:00"},
            {"para": "ana@email.com", "assunto": "Carrinho abandonado - volte!", "tipo": "carrinho", "enviado_em": "2026-08-23T16:00:00"},
            {"para": "lucas@email.com", "assunto": "Pedido #5 confirmado", "tipo": "confirmacao", "enviado_em": "2026-08-24T11:00:00"},
            {"para": "juliana@email.com", "assunto": "Promoção especial para você", "tipo": "promocao", "enviado_em": "2026-08-25T08:00:00"},
            {"para": "carlos@email.com", "assunto": "Pedido #7 enviado", "tipo": "envio", "enviado_em": "2026-08-26T13:00:00"},
            {"para": "beatriz@email.com", "assunto": "Pedido #8 entregue", "tipo": "entrega", "enviado_em": "2026-08-27T10:00:00"},
            {"para": "marcos@email.com", "assunto": "Carrinho abandonado - 10% off", "tipo": "carrinho", "enviado_em": "2026-08-27T18:00:00"},
            {"para": "fernanda@email.com", "assunto": "Pedido #10 confirmado", "tipo": "confirmacao", "enviado_em": "2026-08-28T09:00:00"},
        ]
    )
