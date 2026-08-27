import structlog
from fastapi import APIRouter
from pydantic import BaseModel

from app.models.common import ResponseEnvelope
from app.models.ticket import TicketCaptureRequest, TicketResponse
from app.repositories.ticket_repo import TicketRepository
from app.services.chat_service import processar_ticket
from app.dependencies import get_db

log = structlog.get_logger()

router = APIRouter(prefix="/tickets", tags=["tickets"])


class SequentialChatRequest(BaseModel):
    mensagem: str
    fase: str = "nome"
    campos_pendentes: list[str] = []
    dados_parciais: dict = {}
    tentativas_falhas: int = 0


class SequentialChatResponse(BaseModel):
    mensagem: str
    fase: str
    campos_pendentes: list[str]
    campos_extraidos: list[str]
    dados_parciais: dict
    tentativas_falhas: int
    concluido: bool = False
    encerrado_por_falha: bool = False
    resultado: dict | None = None


@router.post("", response_model=ResponseEnvelope[TicketResponse])
async def capture_ticket(request: TicketCaptureRequest):
    """Create a support ticket (public endpoint — no auth required)."""
    async for session in get_db():
        repo = TicketRepository(session)
        ticket = await repo.create_ticket(
            nome=request.nome,
            email=request.email,
            descricao=request.descricao,
            prioridade=request.prioridade,
        )
        await session.commit()

    log.info("ticket_created", ticket_id=ticket.id, email=request.email)

    return ResponseEnvelope(
        data=TicketResponse(
            id=str(ticket.id),
            nome=ticket.nome,
            email=ticket.email,
            descricao=ticket.descricao,
            prioridade=ticket.prioridade,
            status=ticket.status,
            criado_em=str(ticket.created_at),
        )
    )


@router.post("/chat", response_model=ResponseEnvelope[SequentialChatResponse])
async def ticket_chat(request: SequentialChatRequest):
    """Ticket capture via batch chat with LLM extraction."""
    result = await processar_ticket(
        mensagem=request.mensagem,
        fase=request.fase,
        campos_pendentes=request.campos_pendentes,
        dados_parciais=request.dados_parciais,
        tentativas_falhas=request.tentativas_falhas,
    )
    return ResponseEnvelope(data=SequentialChatResponse(**result))
