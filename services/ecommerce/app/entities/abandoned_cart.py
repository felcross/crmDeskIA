from datetime import datetime

from sqlalchemy import DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AbandonedCart(Base):
    __tablename__ = "abandoned_carts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    cliente_email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    cliente_nome: Mapped[str] = mapped_column(String(255), nullable=False)
    valor_total: Mapped[float] = mapped_column(Float, default=0.0)
    itens_json: Mapped[str] = mapped_column(Text, default="[]")
    criado_em: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
