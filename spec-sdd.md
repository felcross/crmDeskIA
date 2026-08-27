# spec-sdd.md — Addendum 14: Fluxo em Lote

## Specify

### Feature
Fluxo em Lote para os bots de Captura de Lead e Abertura de Chamado.
Em vez de uma pergunta por turno para cada campo, o padrão passa a ser
"nome sozinho primeiro, depois os demais campos pedidos juntos, numa lista".

### Requisitos
1. **Bug fix**: Ambos os bots começam perguntando `nome`, nunca outra coisa.
2. **Turno 1**: Pergunta só `nome`, isoladamente.
3. **Turno 2+**: Após `nome` válido, pede o restante dos campos numa lista
   numerada, numa única mensagem.
4. **Extração multi-campo**: Backend extrai múltiplos campos de uma única
   resposta do usuário via LLM.
5. **Resposta parcial**: Se o usuário responder só parte, bot pede
   especificamente o que falta, sem repetir o que já foi validado.
6. **Contador de tentativas**: "Rodadas sem progresso" (não por campo isolado),
   limite de 3, encerramento determinístico.
7. **Validação por campo**: Regex para email após extração. LLM para nome.
8. **O que não muda**: Resumo de descrição, prioridade hardcoded "media",
   lookup-or-create de empresa, mensagens determinísticas, máquina de estados
   do frontend (IDLE → FLUXO_ATIVO → CONCLUIDO → Recomeçar).

### Não-requisitos
- `telefone` (Lead) continua opcional, nunca perguntado ativamente.
- `prioridade` (Ticket) nunca é perguntada.

---

## Design

### Novo modelo de estado

**Antes (Addendum 13):**
```
campo_atual: str  (um campo por vez)
```

**Depois (Addendum 14):**
```
fase: "nome" | "lote"
campos_pendentes: list[str]
```

### Contrato de API

**Request:**
```python
class SequentialChatRequest(BaseModel):
    mensagem: str
    fase: str = "nome"
    campos_pendentes: list[str] = []
    dados_parciais: dict = {}
    tentativas_falhas: int = 0
```

**Response:**
```python
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
```

### Fluxo

```
Turno 1: User → nome
         Bot  → valida nome via LLM
                se VALIDO: fase="lote", campos_pendentes=[email, empresa, interesse]
                se INVALIDO: tentativas_falhas++, repete pergunta

Turno 2: User → "joao@gmail.com, Acme Ltda, abrir uma conta"
         Bot  → extrai email, empresa, interesse via LLM
                se todos extraídos: concluido=True, cria Lead/Ticket
                se parcial: pede só o que falta

Turno 3+: User → resposta parcial
          Bot  → extrai o que puder, pede restante
                  3 rodadas sem progresso → encerramento determinístico
```

### LLM Prompt de extração em lote

```
Extraia APENAS os seguintes campos: email, empresa, interesse
Mensagem do visitante: "..."
Responda APENAS com JSON: {"email": "...", "empresa": "...", "interesse": "..."}
```

- Temperature: 0.1 (determinístico)
- Validação pós-extração: regex para email
- Proteção: JSON delimitado, sem campos extras aceitos

### Mensagens determinísticas

| Constante | Valor |
|-----------|-------|
| `MSG_BATCH_LEAD` | Lista numerada: e-mail, empresa, interesse |
| `MSG_BATCH_TICKET` | Lista numerada: empresa, cargo, e-mail, descrição |
| `MSG_LIMITE_TENTATIVAS` | (inalterada) Encerramento por falta de informação |
| `MSG_LEAD_CONCLUIDO` | (inalterada) Lead registrado com sucesso |
| `MSG_TICKET_CONCLUIDO` | (inalterada) Chamado registrado com sucesso |

---

## Tasks

| # | Tarefa | Status | Arquivos |
|---|--------|--------|----------|
| T1 | Fix bug greeting (nome primeiro) | ✅ | `Landing.tsx` |
| T2 | Novo contrato de API | ✅ | `leads.py`, `tickets.py`, `api.ts` |
| T3 | Engine de fluxo em lote | ✅ | `chat_service.py` |
| T4 | Atualizar processar_lead/ticket | ✅ | `chat_service.py` |
| T5 | Atualizar endpoints + frontend | ✅ | `leads.py`, `tickets.py`, `InlineChat.tsx` |
| T6 | Testes unitários | ✅ | `test_chat_service.py` (19 testes) |
| T7 | spec-sdd.md | ✅ | Este arquivo |

---

## Execute

### Arquivos modificados

| Arquivo | Mudança |
|---------|---------|
| `frontend/src/features/auth/Landing.tsx` | Greetings perguntam nome primeiro |
| `backend/app/api/v1/leads.py` | Schema `SequentialChatRequest/Response` atualizado |
| `backend/app/api/v1/tickets.py` | Schema `SequentialChatRequest/Response` atualizado |
| `frontend/src/types/api.ts` | Tipos TS atualizados |
| `backend/app/services/chat_service.py` | Engine reescrito: batch extraction, fase nome/lote |
| `backend/tests/unit/test_chat_service.py` | 19 testes cobrindo todos os cenários |

### Critérios de aceite verificados

- [x] Bug corrigido: ambos os bots começam perguntando `nome`
- [x] Turno 1 pergunta só `nome`, isoladamente
- [x] Turno 2 pede restante em lista numerada
- [x] Backend extrai múltiplos campos de uma resposta
- [x] Resposta parcial gera follow-up pedindo só o que falta
- [x] Contador de "rodadas sem progresso" com limite de 3
- [x] Validação por campo (regex email) após extração
- [x] Mensagens determinísticas (nunca geradas pelo LLM)
- [x] 19 testes unitários passando

### Como testar end-to-end

1. Abrir landing page → ambos os bots mostram greeting perguntando nome
2. Digitar nome → bot pede campos restantes em lista numerada
3. Responder tudo → Lead/Ticket criado
4. Responder só email → bot pede só empresa e interesse
5. 3 respostas off-topic → encerramento determinístico
