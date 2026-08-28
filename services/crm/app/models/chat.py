from pydantic import BaseModel


class ChatRequest(BaseModel):
    pergunta: str
    historico: list[dict[str, str]] = []


class ChatChunkEvent(BaseModel):
    chunk: str
    done: bool = False
    chart: dict | None = None
