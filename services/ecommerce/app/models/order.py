from pydantic import BaseModel


class OrderItemResponse(BaseModel):
    id: int
    product_id: int
    product_nome: str
    quantidade: int
    preco_unitario: float


class OrderResponse(BaseModel):
    id: int
    cliente_email: str
    cliente_nome: str
    status: str
    total: float
    qr_code_url: str | None = None
    criado_em: str
    itens: list[OrderItemResponse] = []
