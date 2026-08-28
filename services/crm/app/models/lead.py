from pydantic import BaseModel, EmailStr


class LeadCaptureRequest(BaseModel):
    nome: str
    email: EmailStr
    telefone: str = ""
    interesse: str = ""


class CapturedLeadResponse(BaseModel):
    id: str
    nome: str
    email: str
    telefone: str
    interesse: str
    criado_em: str


class LeadFanOutResult(BaseModel):
    persisted: bool
    notified: bool
    emailed: bool


class ConvertLeadRequest(BaseModel):
    valor: float
    pipeline: str = "default"
    estagio: str = "Prospecção"
