from pydantic import BaseModel, EmailStr


class TicketCaptureRequest(BaseModel):
    nome: str
    email: EmailStr
    descricao: str
    prioridade: str = "normal"


class TicketResponse(BaseModel):
    id: str
    nome: str
    email: str
    descricao: str
    prioridade: str
    status: str
    criado_em: str
