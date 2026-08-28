import json

from fastapi import APIRouter
from fastapi.responses import StreamingResponse

from app.dependencies import get_db
from app.models.chat import ChatRequest
from app.repositories.lead_repo import LeadRepository
from app.services.chat_service import stream_chat
from app.services.deal_service import deal_service

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("")
async def chat(request: ChatRequest):
    deals = await deal_service.get_all_deals(limit=100)

    # Get leads from Postgres
    async for session in get_db():
        lead_repo = LeadRepository(session)
        contacts = await lead_repo.get_all_as_dicts(limit=100)
        break

    async def event_stream():
        async for chunk in stream_chat(request.pergunta, request.historico, deals, contacts):
            yield f"data: {json.dumps(chunk, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
