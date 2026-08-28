from pydantic import BaseModel


class CheckoutItem(BaseModel):
    product_id: int
    quantidade: int


class CheckoutRequest(BaseModel):
    cliente_nome: str
    cliente_email: str
    itens: list[CheckoutItem]


class AbandonedCartRequest(BaseModel):
    cliente_email: str
    cliente_nome: str
    valor_total: float
    itens: list[dict]
