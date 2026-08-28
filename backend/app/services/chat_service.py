"""
Chat Service — Batch bot flow with LLM extraction.

Turn 1: collect name alone.
Turn 2+: request remaining fields as a numbered list, extract multiple
fields from a single user message via LLM.
"""

import json
import re

import structlog
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.config import settings

log = structlog.get_logger()

# ══════════════════════════════════════════════════════════════════════════════
# Field configuration
# ══════════════════════════════════════════════════════════════════════════════

LEAD_FIELDS = ["nome", "email", "empresa", "interesse", "telefone"]
TICKET_FIELDS = ["nome", "empresa", "cargo", "email", "descricao"]

# Fields requested in the batch (after nome), excluding optional ones
LEAD_BATCH_FIELDS = ["email", "empresa", "interesse"]
TICKET_BATCH_FIELDS = ["empresa", "cargo", "email", "descricao"]

# Sequential field order for ticket flow (one at a time)
TICKET_SEQUENTIAL_FIELDS = ["nome", "empresa", "cargo", "email", "descricao"]

OPTIONAL_FIELDS = {"telefone"}

REGEX_VALIDATORS = {
    "email": re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$"),
}

DESCRICAO_MAX_LEN = 500

# ══════════════════════════════════════════════════════════════════════════════
# Deterministic messages
# ══════════════════════════════════════════════════════════════════════════════

MSG_LEAD_CONCLUIDO = (
    "Lead registrado com sucesso! Um especialista entrará em contato em breve."
)
MSG_TICKET_CONCLUIDO = (
    "Chamado registrado com sucesso! Nosso suporte entrará em contato o mais rápido possível."
)
MSG_EMPRESA_NOVA = (
    "Sua empresa não foi encontrada em nosso cadastro — criamos o cadastro agora."
)
MSG_LIMITE_TENTATIVAS = (
    "Não foi possível continuar o atendimento por falta de informação válida."
    " Por favor, inicie novamente."
)

# Per-field questions (used for nome validation and field labels)
FIELD_QUESTIONS = {
    "nome": "Qual o seu nome completo?",
    "email": "e-mail",
    "empresa": "nome da sua empresa",
    "interesse": "seu interesse ou necessidade principal",
    "telefone": "telefone (opcional)",
    "cargo": "seu cargo",
    "descricao": "descrição do problema",
}

# Batch request messages per flow
MSG_BATCH_LEAD = (
    "Para que eu possa encaminhar seu contato ao especialista certo, "
    "preciso apenas de mais alguns detalhes:\n\n"
    "1. E-mail (para enviarmos informações e mantermos o contato);\n"
    "2. Nome da sua empresa;\n"
    "3. Qual é o seu interesse ou necessidade principal (por exemplo, "
    "um produto específico, suporte técnico, orçamento, etc.).\n\n"
    "Pode me passar tudo isso?"
)

MSG_BATCH_TICKET = (
    "Para registrar seu chamado, preciso de mais algumas informações:\n\n"
    "1. Nome da sua empresa;\n"
    "2. Seu cargo;\n"
    "3. Seu e-mail;\n"
    "4. Uma breve descrição do problema que você está enfrentando.\n\n"
    "Pode me passar tudo isso?"
)


# ══════════════════════════════════════════════════════════════════════════════
# LLM factory
# ══════════════════════════════════════════════════════════════════════════════

def _get_llm(temperature: float = 0.3):
    from langchain_groq import ChatGroq

    from app.services.groq_watchdog import schedule_model_check

    try:
        schedule_model_check()
    except Exception:
        pass

    return ChatGroq(
        model=settings.groq_model,
        api_key=settings.groq_api_key,
        temperature=temperature,
    )


# ══════════════════════════════════════════════════════════════════════════════
# LLM validation prompt (for nome phase)
# ══════════════════════════════════════════════════════════════════════════════

def _build_validation_prompt(
    campo: str, mensagem: str, proxima_pergunta: str | None, fluxo: str
) -> list:
    """Build a short LLM prompt to validate a single field value."""
    contexto = "captura de lead" if fluxo == "lead" else "abertura de chamado"

    system = f"""Você é um assistente de {contexto}.
O backend está coletando o campo "{campo}" do visitante.

Mensagem do visitante: "{mensagem}"

Classifique a resposta em uma das categorias abaixo (primeira linha da sua resposta):
VALIDO — a resposta atende ao campo "{campo}"
INVALIDO — a resposta não atende ao campo "{campo}" (formato errado, vazio, sem sentido)
FORA_CONTEXTO — o visitante falou de outro assunto não relacionado

Na segunda linha, escreva UMA frase curta de resposta ao visitante:
- Se VALIDO: confirme brevemente e faça a próxima pergunta:
  {proxima_pergunta or 'Aguarde um momento.'}
- Se INVALIDO: peça educadamente para tentar novamente, explicando o que é esperado
- Se FORA_CONTEXTO: redirecione cordialmente dizendo que está ali para ajudar
  com o {contexto}, e repita a pergunta

Responda APENAS com essas duas linhas, sem markdown, sem formatação extra."""

    return [SystemMessage(content=system), HumanMessage(content=mensagem)]


# ══════════════════════════════════════════════════════════════════════════════
# LLM batch extraction (for lote phase)
# ══════════════════════════════════════════════════════════════════════════════

async def _extract_batch_fields(
    campos_pendentes: list[str], mensagem: str, fluxo: str
) -> dict:
    """Extract multiple fields from a single user message via LLM.

    Returns {
        "extraidos": dict,       # campo -> valor extraído
        "campos_extraidos": list, # campos que foram extraídos com sucesso
        "campos_faltantes": list, # campos que ainda faltam
    }
    """
    campos_str = ", ".join(campos_pendentes)
    contexto = "captura de lead" if fluxo == "lead" else "abertura de chamado"

    system = f"""Você é um assistente de {contexto}.
O visitante enviou uma mensagem com informações pessoais.
Extraia APENAS os seguintes campos: {campos_str}

Mensagem do visitante: "{mensagem}"

Responda APENAS com um JSON no formato:
{{"campo1": "valor1", "campo2": "valor2", ...}}

Regras:
- Inclua SOMENTE os campos listados acima
- Se um campo não aparece na mensagem, use "" (string vazia)
- Não invente valores
- Não adicione campos extras
- Não inclua texto antes ou depois do JSON"""

    llm = _get_llm(temperature=0.1)

    try:
        response = await llm.ainvoke([
            SystemMessage(content=system),
            HumanMessage(content=mensagem),
        ])
        raw = response.content.strip()
    except Exception as e:
        log.error("llm_batch_extraction_error", error=str(e), fluxo=fluxo)
        return {"extraidos": {}, "campos_extraidos": [], "campos_faltantes": campos_pendentes}

    # Parse JSON from response (handle possible markdown wrapping)
    try:
        json_match = re.search(r"\{.*\}", raw, re.DOTALL)
        if not json_match:
            raise ValueError("No JSON found in LLM response")
        extracted = json.loads(json_match.group())
    except (json.JSONDecodeError, ValueError) as e:
        log.error("llm_batch_parse_error", error=str(e), raw=raw[:200], fluxo=fluxo)
        return {"extraidos": {}, "campos_extraidos": [], "campos_faltantes": campos_pendentes}

    # Validate extracted fields
    extraidos = {}
    campos_extraidos = []

    for campo in campos_pendentes:
        valor = extracted.get(campo, "").strip()
        if not valor:
            continue

        # Regex validation for email
        if campo in REGEX_VALIDATORS and not REGEX_VALIDATORS[campo].match(valor):
            log.info("batch_regex_falha", fluxo=fluxo, campo=campo)
            continue

        extraidos[campo] = valor
        campos_extraidos.append(campo)

    campos_faltantes = [c for c in campos_pendentes if c not in campos_extraidos]

    log.info(
        "batch_extraction",
        fluxo=fluxo,
        extraidos=campos_extraidos,
        faltantes=campos_faltantes,
    )

    return {
        "extraidos": extraidos,
        "campos_extraidos": campos_extraidos,
        "campos_faltantes": campos_faltantes,
    }


def _build_followup_message(campos_faltantes: list[str]) -> str:
    """Build a follow-up message asking only for missing fields."""
    labels = []
    for c in campos_faltantes:
        label = FIELD_QUESTIONS.get(c, c)
        labels.append(label)

    if len(labels) == 1:
        return f"Ainda preciso do {labels[0]} — pode me informar?"
    elif len(labels) == 2:
        return f"Ainda preciso do {labels[0]} e do {labels[1]} — pode complementar?"
    else:
        items = ", ".join(labels[:-1]) + f" e {labels[-1]}"
        return f"Ainda preciso de {items} — pode complementar?"


# ══════════════════════════════════════════════════════════════════════════════
# Sequential field extraction (one field at a time)
# ══════════════════════════════════════════════════════════════════════════════

async def _extract_single_field(
    campo: str, mensagem: str, fluxo: str
) -> str | None:
    """Extract a single field value from user message via LLM.

    Returns the extracted value or None if not found/invalid.
    """
    contexto = "captura de lead" if fluxo == "lead" else "abertura de chamado"
    label = FIELD_QUESTIONS.get(campo, campo)

    system = f"""Você é um assistente de {contexto}.
O visitante está respondendo a pergunta sobre "{label}".

Mensagem do visitante: "{mensagem}"

Extraia o valor do campo "{campo}" da mensagem.
Responda APENAS com o valor extraído, sem formatação extra.
Se a mensagem não contiver uma resposta válida para "{campo}", responda apenas: INVALIDO"""

    llm = _get_llm(temperature=0.1)

    try:
        response = await llm.ainvoke([
            SystemMessage(content=system),
            HumanMessage(content=mensagem),
        ])
        raw = response.content.strip()
    except Exception as e:
        log.error("llm_single_field_error", error=str(e), fluxo=fluxo, campo=campo)
        return None

    if raw.upper() == "INVALIDO" or not raw:
        return None

    # Regex validation for email
    if campo in REGEX_VALIDATORS and not REGEX_VALIDATORS[campo].match(raw):
        return None

    return raw


# ══════════════════════════════════════════════════════════════════════════════
# LLM summarization (for descricao > 500 chars)
# ══════════════════════════════════════════════════════════════════════════════

async def _summarize_text(text: str, max_len: int = DESCRICAO_MAX_LEN) -> str:
    """Use LLM to summarize text to fit within max_len characters."""
    llm = _get_llm(temperature=0.2)
    messages = [
        SystemMessage(
            content=f"Resuma o texto a seguir em no máximo {max_len} caracteres, "
            f"mantendo as informações mais importantes. Responda APENAS com o resumo."
        ),
        HumanMessage(content=text),
    ]
    response = await llm.ainvoke(messages)
    return response.content.strip()[:max_len]


# ══════════════════════════════════════════════════════════════════════════════
# Core batch flow engine
# ══════════════════════════════════════════════════════════════════════════════

async def processar_mensagem_bot(
    mensagem: str,
    fase: str,
    campos_pendentes: list[str],
    dados_parciais: dict,
    tentativas_falhas: int,
    fluxo: str,
) -> dict:
    """Process one message in the batch bot flow.

    Returns dict matching SequentialChatResponse schema.
    """
    if fase == "nome":
        return await _processar_fase_nome(
            mensagem, dados_parciais, tentativas_falhas, fluxo
        )
    else:
        return await _processar_fase_lote(
            mensagem, campos_pendentes, dados_parciais, tentativas_falhas, fluxo
        )


async def _processar_fase_lote(
    mensagem: str,
    campos_pendentes: list[str],
    dados_parciais: dict,
    tentativas_falhas: int,
    fluxo: str,
) -> dict:
    """Process a message in the batch phase — extract multiple fields."""
    # Check attempt limit (rounds without progress)
    if tentativas_falhas >= 3:
        log.info("bot_limite_tentativas", fluxo=fluxo, fase="lote")
        return {
            "mensagem": MSG_LIMITE_TENTATIVAS,
            "fase": "lote",
            "campos_pendentes": campos_pendentes,
            "campos_extraidos": [],
            "dados_parciais": dados_parciais,
            "tentativas_falhas": tentativas_falhas,
            "concluido": True,
            "encerrado_por_falha": True,
            "resultado": None,
        }

    # Extract batch fields via LLM
    result = await _extract_batch_fields(campos_pendentes, mensagem, fluxo)
    extraidos = result["extraidos"]
    campos_extraidos = result["campos_extraidos"]
    campos_faltantes = result["campos_faltantes"]

    # Update dados_parciais with extracted fields
    for campo, valor in extraidos.items():
        dados_parciais[campo] = valor

    if campos_extraidos:
        # At least one field extracted — progress made, reset counter
        tentativas_falhas = 0
    else:
        # No fields extracted — count as round without progress
        tentativas_falhas += 1

    # Check if all batch fields collected
    if not campos_faltantes:
        log.info("bot_campos_completos", fluxo=fluxo, dados=dados_parciais)
        return {
            "mensagem": "",
            "fase": "lote",
            "campos_pendentes": [],
            "campos_extraidos": campos_extraidos,
            "dados_parciais": dados_parciais,
            "tentativas_falhas": 0,
            "concluido": True,
            "encerrado_por_falha": False,
            "resultado": None,
        }

    # Build follow-up message for missing fields
    followup = _build_followup_message(campos_faltantes)
    return {
        "mensagem": followup,
        "fase": "lote",
        "campos_pendentes": campos_faltantes,
        "campos_extraidos": campos_extraidos,
        "dados_parciais": dados_parciais,
        "tentativas_falhas": tentativas_falhas,
        "concluido": False,
        "encerrado_por_falha": False,
        "resultado": None,
    }


async def _processar_fase_nome(
    mensagem: str,
    dados_parciais: dict,
    tentativas_falhas: int,
    fluxo: str,
) -> dict:
    """Process a message in the nome phase — validate name via LLM."""
    # Check attempt limit
    if tentativas_falhas >= 3:
        log.info("bot_limite_tentativas", fluxo=fluxo, fase="nome")
        return {
            "mensagem": MSG_LIMITE_TENTATIVAS,
            "fase": "nome",
            "campos_pendentes": [],
            "campos_extraidos": [],
            "dados_parciais": dados_parciais,
            "tentativas_falhas": tentativas_falhas,
            "concluido": True,
            "encerrado_por_falha": True,
            "resultado": None,
        }

    # Validate nome via LLM
    batch_fields = LEAD_BATCH_FIELDS if fluxo == "lead" else TICKET_BATCH_FIELDS
    batch_msg = MSG_BATCH_LEAD if fluxo == "lead" else MSG_BATCH_TICKET

    prompt = _build_validation_prompt("nome", mensagem, batch_msg, fluxo)
    llm = _get_llm()

    try:
        response = await llm.ainvoke(prompt)
        raw = response.content.strip()
    except Exception as e:
        log.error("llm_call_error", error=str(e), fluxo=fluxo, fase="nome")
        return {
            "mensagem": "Desculpe, tive um problema técnico. Pode repetir seu nome?",
            "fase": "nome",
            "campos_pendentes": [],
            "campos_extraidos": [],
            "dados_parciais": dados_parciais,
            "tentativas_falhas": tentativas_falhas,
            "concluido": False,
            "encerrado_por_falha": False,
            "resultado": None,
        }

    # Parse LLM response
    lines = raw.split("\n", 1)
    classification = lines[0].strip().upper()
    bot_message = lines[1].strip() if len(lines) > 1 else ""

    if classification.startswith("VALIDO"):
        dados_parciais["nome"] = mensagem.strip()
        log.info("bot_nome_validado", fluxo=fluxo, nome=mensagem.strip())
        # Transition to batch phase
        return {
            "mensagem": bot_message or batch_msg,
            "fase": "lote",
            "campos_pendentes": batch_fields,
            "campos_extraidos": ["nome"],
            "dados_parciais": dados_parciais,
            "tentativas_falhas": 0,
            "concluido": False,
            "encerrado_por_falha": False,
            "resultado": None,
        }
    else:
        log.info("bot_nome_falha", fluxo=fluxo, classificacao=classification)
        if not bot_message:
            bot_message = "Pode me dizer seu nome completo?"
        return {
            "mensagem": bot_message,
            "fase": "nome",
            "campos_pendentes": [],
            "campos_extraidos": [],
            "dados_parciais": dados_parciais,
            "tentativas_falhas": tentativas_falhas + 1,
            "concluido": False,
            "encerrado_por_falha": False,
            "resultado": None,
        }


# ══════════════════════════════════════════════════════════════════════════════
# Lead capture — full flow
# ══════════════════════════════════════════════════════════════════════════════

async def processar_lead(
    mensagem: str,
    fase: str,
    campos_pendentes: list[str],
    dados_parciais: dict,
    tentativas_falhas: int,
) -> dict:
    """Process a lead capture message."""
    result = await processar_mensagem_bot(
        mensagem, fase, campos_pendentes, dados_parciais, tentativas_falhas, fluxo="lead"
    )

    if result["concluido"] and not result["encerrado_por_falha"]:
        from app.services.lead_service import lead_service

        dados = result["dados_parciais"]
        entity_result = await lead_service.capture_lead(
            nome=dados.get("nome", ""),
            email=dados.get("email", ""),
            telefone=dados.get("telefone", ""),
            interesse=dados.get("interesse", ""),
        )
        result["mensagem"] = MSG_LEAD_CONCLUIDO
        result["resultado"] = entity_result

    return result


# ══════════════════════════════════════════════════════════════════════════════
# Ticket capture — sequential flow (one field at a time)
# ══════════════════════════════════════════════════════════════════════════════

MSG_ATENDIMENTO_CONCLUIDO = (
    "Atendimento registrado com sucesso! Nosso time entrará em contato o mais rápido possível."
)

# Next field after each phase
_TICKET_NEXT_FIELD = {
    "nome": "empresa",
    "empresa": "cargo",
    "cargo": "email",
    "email": "descricao",
    "descricao": None,  # all fields collected
}


async def processar_ticket(
    mensagem: str,
    fase: str,
    campos_pendentes: list[str],
    dados_parciais: dict,
    tentativas_falhas: int,
) -> dict:
    """Process a ticket capture message — sequential one-field-at-a-time flow.

    Flow: nome → empresa → cargo → email → descricao → create lead + ticket.
    """
    # Check attempt limit
    if tentativas_falhas >= 3:
        log.info("ticket_limite_tentativas", fase=fase)
        return {
            "mensagem": MSG_LIMITE_TENTATIVAS,
            "fase": fase,
            "campos_pendentes": [],
            "campos_extraidos": [],
            "dados_parciais": dados_parciais,
            "tentativas_falhas": tentativas_falhas,
            "concluido": True,
            "encerrado_por_falha": True,
            "resultado": None,
        }

    # Extract the current field
    valor = await _extract_single_field(fase, mensagem, "ticket")

    if valor is None:
        # Field not valid — ask again
        label = FIELD_QUESTIONS.get(fase, fase)
        tentativas_falhas += 1
        if tentativas_falhas >= 3:
            log.info("ticket_limite_tentativas", fase=fase)
            return {
                "mensagem": MSG_LIMITE_TENTATIVAS,
                "fase": fase,
                "campos_pendentes": [],
                "campos_extraidos": [],
                "dados_parciais": dados_parciais,
                "tentativas_falhas": tentativas_falhas,
                "concluido": True,
                "encerrado_por_falha": True,
                "resultado": None,
            }
        return {
            "mensagem": f"Não consegui identificar o {label}. Pode informar novamente?",
            "fase": fase,
            "campos_pendentes": [],
            "campos_extraidos": [],
            "dados_parciais": dados_parciais,
            "tentativas_falhas": tentativas_falhas,
            "concluido": False,
            "encerrado_por_falha": False,
            "resultado": None,
        }

    # Field extracted successfully
    dados_parciais[fase] = valor
    log.info("ticket_field_extracted", fase=fase, valor=valor)

    # Determine next phase
    next_fase = _TICKET_NEXT_FIELD.get(fase)

    if next_fase is not None:
        # Ask next field
        next_label = FIELD_QUESTIONS.get(next_fase, next_fase)
        return {
            "mensagem": f"Qual o {next_label}?",
            "fase": next_fase,
            "campos_pendentes": [],
            "campos_extraidos": [fase],
            "dados_parciais": dados_parciais,
            "tentativas_falhas": 0,
            "concluido": False,
            "encerrado_por_falha": False,
            "resultado": None,
        }

    # All fields collected — create lead + ticket
    return await _finalizar_atendimento(dados_parciais)


async def _finalizar_atendimento(dados_parciais: dict) -> dict:
    """Create lead (if needed) + ticket from collected data."""
    from app.dependencies import get_db
    from app.repositories.company_repo import CompanyRepository
    from app.repositories.lead_repo import LeadRepository
    from app.repositories.ticket_repo import TicketRepository

    dados = dados_parciais
    descricao = dados.get("descricao", "")

    if len(descricao) > DESCRICAO_MAX_LEN:
        descricao = await _summarize_text(descricao)

    empresa_nome = dados.get("empresa", "")
    email = dados.get("email", "")
    nome = dados.get("nome", "")
    cargo = dados.get("cargo", "")
    empresa_msg = ""

    async for session in get_db():
        lead_repo = LeadRepository(session)
        company_repo = CompanyRepository(session)
        ticket_repo = TicketRepository(session)

        # Look up lead by email
        lead = await lead_repo.get_by_email(email) if email else None
        if lead is None:
            lead = await lead_repo.create_lead(
                nome=nome,
                email=email,
                status_lead="novo",
            )
            log.info("lead_created_from_ticket", lead_id=lead.id, email=email)

        # Look up or create company
        company = await company_repo.get_by_nome_case_insensitive(empresa_nome)
        if company is None:
            company = await company_repo.create_company(
                nome=empresa_nome, origem="chamado_automatico"
            )
            empresa_msg = f"\n\n{MSG_EMPRESA_NOVA}"

        # Create ticket linked to lead
        ticket = await ticket_repo.create_ticket(
            nome=nome,
            email=email,
            descricao=descricao,
            prioridade="media",
            cargo=cargo,
            company_id=company.id,
            lead_id=lead.id,
        )
        await session.commit()

    log.info("atendimento_finalizado", ticket_id=ticket.id, lead_id=lead.id, email=email)

    return {
        "mensagem": MSG_ATENDIMENTO_CONCLUIDO + empresa_msg,
        "fase": "descricao",
        "campos_pendentes": [],
        "campos_extraidos": ["descricao"],
        "dados_parciais": dados_parciais,
        "tentativas_falhas": 0,
        "concluido": True,
        "encerrado_por_falha": False,
        "resultado": {
            "id": str(ticket.id),
            "nome": ticket.nome,
            "email": ticket.email,
            "descricao": ticket.descricao,
            "prioridade": ticket.prioridade,
            "status": ticket.status,
            "cargo": ticket.cargo,
            "company_id": ticket.company_id,
            "lead_id": lead.id,
            "criado_em": str(ticket.created_at),
        },
    }


# ══════════════════════════════════════════════════════════════════════════════
# Analytical chat (existing — unchanged)
# ══════════════════════════════════════════════════════════════════════════════

SYSTEM_ANALITICO = """Você é um assistente de análise de dados de CRM.
Responda perguntas sobre deals, contatos e pipeline de vendas de forma clara e objetiva.
Use os dados fornecidos para fundamentar suas respostas.
Se o usuário pedir um gráfico, indique no início da resposta com [CHART:tipo].
Responda em português."""


def _detect_chart(text: str) -> dict | None:
    import re as _re
    match = _re.search(r"\[CHART:(\w+)\]", text)
    if match:
        return {"type": match.group(1)}
    return None


async def stream_chat(
    pergunta: str, historico: list[dict], deals: list[dict], contacts: list[dict]
):
    """Stream chat response chunks (analytical chat — unchanged)."""
    import json as _json
    llm = _get_llm(temperature=0.3)

    deals_json = _json.dumps(deals[:50], ensure_ascii=False)
    contacts_json = _json.dumps(contacts[:50], ensure_ascii=False)
    dados = f"DEALS:\n{deals_json}\n\nCONTATOS:\n{contacts_json}"

    messages = [SystemMessage(content=f"{SYSTEM_ANALITICO}\n\n{dados}")]
    for msg in historico[-6:]:
        if msg.get("role") == "user":
            messages.append(HumanMessage(content=msg["content"]))
        else:
            messages.append(AIMessage(content=msg["content"]))
    messages.append(HumanMessage(content=pergunta))

    full_response = ""
    async for chunk in llm.astream(messages):
        if chunk.content:
            full_response += chunk.content
            yield {"chunk": chunk.content, "done": False}

    chart = _detect_chart(full_response)
    yield {"chunk": "", "done": True, "chart": chart}
