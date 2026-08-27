"""
Lead Service — Lead capture + fan-out orchestration.
"""

import structlog

from app.dependencies import get_db
from app.events.publisher import event_publisher
from app.repositories.captured_lead_repo import CapturedLeadRepository

log = structlog.get_logger()


class LeadService:
    """Orchestrates lead capture and fan-out to consumers."""

    async def capture_lead(
        self,
        nome: str,
        email: str,
        telefone: str = "",
        interesse: str = "",
        resumo_conversa: str = "",
    ) -> dict:
        """
        Capture a lead:
        1. Persist in Postgres
        2. Fan-out event (SSE notify + email)
        """
        # Persist in Postgres
        async for session in get_db():
            repo = CapturedLeadRepository(session)
            lead = await repo.create_lead(
                nome=nome,
                email=email,
                telefone=telefone,
                interesse=interesse,
            )
            await session.commit()

        lead_data = {
            "nome": nome,
            "email": email,
            "telefone": telefone,
            "interesse": interesse,
        }

        # Fan-out via Redis Pub/Sub
        try:
            await event_publisher.publish_lead_captured(lead_data)
        except Exception as e:
            log.error("Fan-out publish failed", error=str(e))

        return {
            "id": str(lead.id),
            "nome": nome,
            "email": email,
            "telefone": telefone,
            "interesse": interesse,
            "criado_em": str(lead.created_at),
        }


lead_service = LeadService()
