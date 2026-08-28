import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.common import ResponseEnvelope
from app.models.order import OrderItemResponse, OrderResponse
from app.repositories.order_repo import OrderRepository

log = structlog.get_logger()
router = APIRouter(prefix="/orders", tags=["orders"])


@router.get("", response_model=ResponseEnvelope)
async def list_orders(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status: str | None = Query(None),
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    repo = OrderRepository(db)
    offset = (page - 1) * page_size
    orders = await repo.get_all(limit=page_size, offset=offset, status=status)
    return ResponseEnvelope(data=[_order_to_response(o) for o in orders])


@router.get("/{order_id}", response_model=ResponseEnvelope)
async def get_order(order_id: int, db: AsyncSession = Depends(get_db)):  # noqa: B008
    repo = OrderRepository(db)
    order = await repo.get_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return ResponseEnvelope(data=_order_to_response(order))


def _order_to_response(order) -> OrderResponse:
    return OrderResponse(
        id=order.id,
        cliente_email=order.cliente_email,
        cliente_nome=order.cliente_nome,
        status=order.status,
        total=order.total,
        qr_code_url=order.qr_code_url,
        criado_em=str(order.criado_em),
        itens=[
            OrderItemResponse(
                id=item.id,
                product_id=item.product_id,
                product_nome=f"Produto #{item.product_id}",
                quantidade=item.quantidade,
                preco_unitario=item.preco_unitario,
            )
            for item in (order.itens or [])
        ],
    )
