import httpx
from fastapi import Response

_EXCLUDED_HEADERS = {"content-length", "transfer-encoding", "connection"}


def build_proxy_response(resp: httpx.Response) -> Response:
    """Monta uma Response do Starlette a partir de uma resposta do httpx,
    preservando todos os headers, inclusive repetidos (ex: múltiplos Set-Cookie)."""
    response = Response(content=resp.content, status_code=resp.status_code)
    for key, value in resp.headers.multi_items():
        if key.lower() not in _EXCLUDED_HEADERS:
            response.headers.append(key, value)
    return response