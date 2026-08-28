from pydantic import BaseModel


class ResponseEnvelope(BaseModel):
    data: object | None = None
    error: object | None = None
    meta: dict | None = None
