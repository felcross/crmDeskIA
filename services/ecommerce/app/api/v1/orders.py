import json

import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.entities.abandoned_cart import AbandonedCart
from app.entities.email_log import EmailLog
from app.entities.order import Order
from app.entities.order_item import OrderItem
from app.models.checkout import AbandonedCartRequest, CheckoutRequest
from app.models.common import ResponseEnvelope
from app.models.order import OrderItemResponse, OrderResponse
from app.repositories.order_repo import OrderRepository
from app.repositories.product_repo import ProductRepository

log = structlog.get_logger()
router = APIRouter(prefix="/orders", tags=["orders"])

QR_BASE = "https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=PEDIDO-"


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


@router.post("", response_model=ResponseEnvelope, status_code=201)
async def create_order(req: CheckoutRequest, db: AsyncSession = Depends(get_db)):  # noqa: B008
    """Checkout: create order, reduce stock, generate QR, log fake email."""
    product_repo = ProductRepository(db)

    # Validate items and calculate total
    total = 0.0
    order_items_data = []
    for item in req.itens:
        product = await product_repo.get_by_id(item.product_id)
        if not product:
            raise HTTPException(status_code=400, detail=f"Product {item.product_id} not found")
        if not product.ativo:
            raise HTTPException(status_code=400, detail=f"Product {product.nome} is inactive")
        if product.estoque < item.quantidade:
            raise HTTPException(
                status_code=400,
                detail=f"Insufficient stock for {product.nome}: available {product.estoque}, requested {item.quantidade}",
            )
        subtotal = product.preco * item.quantidade
        total += subtotal
        order_items_data.append({
            "product": product,
            "quantidade": item.quantidade,
            "preco_unitario": product.preco,
        })

    # Create order
    order = Order(
        cliente_email=req.cliente_email,
        cliente_nome=req.cliente_nome,
        status="pago",
        total=round(total, 2),
        qr_code_url=f"{QR_BASE}{req.cliente_email}",
    )
    db.add(order)
    await db.flush()

    # Create order items and reduce stock
    for data in order_items_data:
        product = data["product"]
        order_item = OrderItem(
            order_id=order.id,
            product_id=product.id,
            quantidade=data["quantidade"],
            preco_unitario=data["preco_unitario"],
        )
        db.add(order_item)
        product.estoque -= data["quantidade"]

    # Log fake email
    email_log = EmailLog(
        para=req.cliente_email,
        assunto=f"Pedido #{order.id} confirmado — QR Code para pagamento",
        tipo="confirmacao",
    )
    db.add(email_log)

    await db.commit()

    log.info("order_created", order_id=order.id, email=req.cliente_email, total=order.total)

    # Reload with items
    order_repo = OrderRepository(db)
    order = await order_repo.get_by_id(order.id)
    return ResponseEnvelope(data=_order_to_response(order))


@router.post("/abandoned", status_code=201)
async def register_abandoned_cart(req: AbandonedCartRequest, db: AsyncSession = Depends(get_db)):  # noqa: B008
    """Register an abandoned cart for CRM/ERP tracking."""
    cart = AbandonedCart(
        cliente_email=req.cliente_email,
        cliente_nome=req.cliente_nome,
        valor_total=req.valor_total,
        itens_json=json.dumps(req.itens, ensure_ascii=False),
    )
    db.add(cart)
    await db.commit()

    log.info("abandoned_cart_registered", email=req.cliente_email, valor=req.valor_total)
    return {"data": {"id": cart.id, "message": "Carrinho abandonado registrado"}}


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
