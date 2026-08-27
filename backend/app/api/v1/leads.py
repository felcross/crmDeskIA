import structlog
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.dependencies import get_db
from app.models.common import ResponseEnvelope
from app.models.dashboard import DealResponse
from app.models.lead import CapturedLeadResponse, ConvertLeadRequest, LeadCaptureRequest, LeadFanOutResult
from app.repositories.deal_repo import DealRepository
from app.repositories.lead_repo import LeadRepository
from app.services.chat_service import processar_lead
from app.services.lead_service import lead_service

log = structlog.get_logger()

router = APIRouter(prefix="/leads", tags=["leads"])


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


@router.post("", response_model=ResponseEnvelope[CapturedLeadResponse])
async def capture_lead(request: LeadCaptureRequest):
    result = await lead_service.capture_lead(
        nome=request.nome,
        email=request.email,
        telefone=request.telefone,
        interesse=request.interesse,
    )
    return ResponseEnvelope(data=CapturedLeadResponse(**result))


@router.post("/chat", response_model=ResponseEnvelope[SequentialChatResponse])
async def lead_chat(request: SequentialChatRequest):
    """Lead capture via batch chat with LLM extraction."""
    result = await processar_lead(
        mensagem=request.mensagem,
        fase=request.fase,
        campos_pendentes=request.campos_pendentes,
        dados_parciais=request.dados_parciais,
        tentativas_falhas=request.tentativas_falhas,
    )
    return ResponseEnvelope(data=SequentialChatResponse(**result))


@router.post("/fan-out-test", response_model=ResponseEnvelope[LeadFanOutResult])
async def test_fan_out():
    """Test endpoint for fan-out mechanism."""
    from app.events.publisher import event_publisher

    test_data = {
        "nome": "Test Lead",
        "email": "test@example.com",
        "telefone": "+5511999999999",
        "interesse": "Test",
    }
    await event_publisher.publish_lead_captured(test_data)
    return ResponseEnvelope(
        data=LeadFanOutResult(persisted=True, notified=True, emailed=False)
    )


@router.post("/{lead_id}/convert", response_model=ResponseEnvelope[DealResponse])
async def convert_lead(
    lead_id: int,
    request: ConvertLeadRequest,
    db: AsyncSession = Depends(get_db),
):
    """Convert a lead into a deal."""
    lead_repo = LeadRepository(db)
    deal_repo = DealRepository(db)

    lead = await lead_repo.get_by_id(lead_id)
    if lead is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Lead not found",
        )

    existing = await deal_repo.get_by_lead_id(lead_id)
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Lead already converted to a deal",
        )

    deal = await deal_repo.create_deal(
        nome=lead.nome,
        valor=request.valor,
        estagio=request.estagio,
        pipeline=request.pipeline,
        lead_id=lead.id,
    )
    await db.commit()

    log.info("lead_converted", lead_id=lead_id, deal_id=deal.id, valor=request.valor)

    return ResponseEnvelope(
        data=DealResponse(
            id=str(deal.id),
            nome=deal.nome,
            valor=deal.valor,
            estagio=deal.estagio,
            pipeline=deal.pipeline,
            data_close=str(deal.data_close) if deal.data_close else "",
            criado_em=str(deal.criado_em),
        )
    )
