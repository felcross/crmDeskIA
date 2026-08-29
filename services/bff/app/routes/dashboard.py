import asyncio

import httpx
import structlog
from fastapi import APIRouter, Request, Response
from app.proxy_utils import build_proxy_response
from app.config import settings

log = structlog.get_logger()
router = APIRouter(tags=["dashboard"])


async def _call_service(url: str) -> dict | list | None:
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(url)
            if resp.status_code == 200:
                body = resp.json()
                return body.get("data", body)
    except (httpx.ConnectError, httpx.TimeoutException) as e:
        log.warning("service_call_failed", url=url, error=str(e))
    return None


@router.get("/dashboard/kpis")
async def get_dashboard_kpis():
    """Aggregate KPIs from CRM + E-commerce."""
    crm_url = f"{settings.crm_backend_url}/api/v1/dashboard/kpis"
    stats_url = f"{settings.ecommerce_backend_url}/api/v1/internal/stats"
    low_stock_url = f"{settings.ecommerce_backend_url}/api/v1/internal/products/low-stock"
    abandoned_url = f"{settings.ecommerce_backend_url}/api/v1/internal/carts/abandoned"

    _crm_kpis, ecom_stats, low_stock, abandoned = await asyncio.gather(
        _call_service(crm_url),
        _call_service(stats_url),
        _call_service(low_stock_url),
        _call_service(abandoned_url),
    )

    stats = ecom_stats or {}
    low_stock_list = low_stock or []
    abandoned_list = abandoned or []

    kpis = [
        {"title": "Faturamento Total", "value": stats.get("faturamento_total", 0)},
        {"title": "Faturamento Mês", "value": stats.get("faturamento_mes", 0)},
        {"title": "Pedidos Abertos", "value": stats.get("pedidos_abertos", 0)},
        {"title": "Pedidos Fechados", "value": stats.get("pedidos_fechados", 0)},
        {"title": "Ticket Médio", "value": stats.get("ticket_medio", 0)},
        {"title": "Estoque Baixo", "value": len(low_stock_list)},
        {"title": "Carrinhos Abandonados", "value": len(abandoned_list)},
    ]

    return {"data": kpis, "error": None}


@router.get("/dashboard/charts")
async def get_dashboard_charts():
    """Proxy charts from CRM backend."""
    url = f"{settings.crm_backend_url}/api/v1/dashboard/charts"
    data = await _call_service(url)
    return {"data": data, "error": None}


# --- Proxy endpoints for e-commerce data via BFF ---

@router.api_route("/dashboard/products", methods=["GET", "PATCH"])
async def proxy_products(request: Request):
    """Proxy product requests to e-commerce backend."""
    path = "products"
    if request.url.query:
        path += f"?{request.url.query}"
    target = f"{settings.ecommerce_backend_url}/api/v1/{path}"

    headers = dict(request.headers)
    headers.pop("host", None)
    body = await request.body()

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.request(
                method=request.method,
                url=target,
                headers=headers,
                content=body,
            )
             return build_proxy_response(resp)
            
        except httpx.ConnectError:
             return build_proxy_response(resp)


@router.api_route("/dashboard/products/{product_id}", methods=["GET", "PATCH"])
async def proxy_product_detail(product_id: int, request: Request):
    """Proxy single product requests to e-commerce backend."""
    target = f"{settings.ecommerce_backend_url}/api/v1/products/{product_id}"

    headers = dict(request.headers)
    headers.pop("host", None)
    body = await request.body()

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.request(
                method=request.method,
                url=target,
                headers=headers,
                content=body,
            )
             return build_proxy_response(resp)

        except httpx.ConnectError:

             return build_proxy_response(resp)


@router.get("/dashboard/orders")
async def proxy_orders(request: Request):
    """Proxy order list to e-commerce backend."""
    path = "orders"
    if request.url.query:
        path += f"?{request.url.query}"
    target = f"{settings.ecommerce_backend_url}/api/v1/{path}"

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(target)
             return build_proxy_response(resp)

        except httpx.ConnectError:
             return build_proxy_response(resp)


@router.get("/dashboard/orders/{order_id}")
async def proxy_order_detail(order_id: int):
    """Proxy single order to e-commerce backend."""
    target = f"{settings.ecommerce_backend_url}/api/v1/orders/{order_id}"

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(target)
             return build_proxy_response(resp)

        except httpx.ConnectError:
             return build_proxy_response(resp)

@router.get("/dashboard/customers")
async def proxy_customers():
    """Proxy customer list from e-commerce internal API."""
    orders_target = f"{settings.ecommerce_backend_url}/api/v1/orders?page_size=100"
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            resp = await client.get(orders_target)
            if resp.status_code == 200:
                body = resp.json()
                orders = body.get("data", [])
                # Aggregate customers from orders
                customers = {}
                for order in orders:
                    email = order.get("cliente_email", "")
                    if email not in customers:
                        customers[email] = {
                            "email": email,
                            "nome": order.get("cliente_nome", ""),
                            "total_pedidos": 0,
                            "total_gasto": 0,
                        }
                    customers[email]["total_pedidos"] += 1
                    customers[email]["total_gasto"] += order.get("total", 0)

                return {"data": list(customers.values()), "error": None}
        except httpx.ConnectError:
            pass

    return {"data": [], "error": None}
