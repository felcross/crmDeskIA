from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Deal(Base):
    __tablename__ = "deals"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    valor: Mapped[float] = mapped_column(Float, default=0.0)
    estagio: Mapped[str] = mapped_column(String(100), nullable=False)
    pipeline: Mapped[str] = mapped_column(String(100), default="")
    data_close: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    lead_id: Mapped[int | None] = mapped_column(ForeignKey("leads.id"), nullable=True)
