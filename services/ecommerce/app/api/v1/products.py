import structlog
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.models.common import ResponseEnvelope
from app.models.product import ProductResponse, ProductUpdate
from app.repositories.product_repo import ProductRepository

log = structlog.get_logger()
router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=ResponseEnvelope)
async def list_products(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    repo = ProductRepository(db)
    offset = (page - 1) * page_size
    products = await repo.get_all(limit=page_size, offset=offset)
    return ResponseEnvelope(
        data=[
            ProductResponse(
                id=p.id,
                nome=p.nome,
                descricao=p.descricao or "",
                preco=p.preco,
                estoque=p.estoque,
                imagem_url=p.imagem_url,
                ativo=p.ativo,
                criado_em=str(p.criado_em),
            )
            for p in products
        ]
    )


@router.get("/{product_id}", response_model=ResponseEnvelope)
async def get_product(product_id: int, db: AsyncSession = Depends(get_db)):  # noqa: B008
    repo = ProductRepository(db)
    product = await repo.get_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return ResponseEnvelope(
        data=ProductResponse(
            id=product.id,
            nome=product.nome,
            descricao=product.descricao or "",
            preco=product.preco,
            estoque=product.estoque,
            imagem_url=product.imagem_url,
            ativo=product.ativo,
            criado_em=str(product.criado_em),
        )
    )


@router.patch("/{product_id}", response_model=ResponseEnvelope)
async def update_product(
    product_id: int,
    update: ProductUpdate,
    db: AsyncSession = Depends(get_db),  # noqa: B008
):
    repo = ProductRepository(db)
    product = await repo.get_by_id(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    data = update.model_dump(exclude_unset=True)
    if not data:
        raise HTTPException(status_code=400, detail="No fields to update")

    product = await repo.update(product, data)
    await db.commit()

    log.info("product_updated", product_id=product_id, fields=list(data.keys()))
    return ResponseEnvelope(
        data=ProductResponse(
            id=product.id,
            nome=product.nome,
            descricao=product.descricao or "",
            preco=product.preco,
            estoque=product.estoque,
            imagem_url=product.imagem_url,
            ativo=product.ativo,
            criado_em=str(product.criado_em),
        )
    )
