from pydantic import BaseModel


class ProductResponse(BaseModel):
    id: int
    nome: str
    descricao: str
    preco: float
    estoque: int
    imagem_url: str | None = None
    ativo: bool
    criado_em: str


class ProductUpdate(BaseModel):
    nome: str | None = None
    descricao: str | None = None
    preco: float | None = None
    estoque: int | None = None
    ativo: bool | None = None
