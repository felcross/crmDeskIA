from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Company(Base):
    __tablename__ = "companies"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    origem: Mapped[str] = mapped_column(String(50), nullable=False)  # "negocio_fechado" | "chamado_automatico"
    deal_id: Mapped[int | None] = mapped_column(ForeignKey("deals.id"), nullable=True)
    criado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
