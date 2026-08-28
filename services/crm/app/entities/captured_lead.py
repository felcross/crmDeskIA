from datetime import datetime

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class CapturedLead(Base):
    __tablename__ = "captured_leads"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    telefone: Mapped[str] = mapped_column(String(50), default="")
    interesse: Mapped[str] = mapped_column(Text, default="")
    hubspot_contact_id: Mapped[str | None] = mapped_column(String(50), nullable=True)
    captured_by_user_id: Mapped[int | None] = mapped_column(nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
