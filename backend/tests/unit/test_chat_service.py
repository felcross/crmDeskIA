"""Tests for the batch bot flow engine."""

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.chat_service import (
    LEAD_BATCH_FIELDS,
    MSG_LIMITE_TENTATIVAS,
    TICKET_BATCH_FIELDS,
    _build_followup_message,
    _extract_batch_fields,
    _processar_fase_lote,
    _processar_fase_nome,
    processar_mensagem_bot,
)


def _mock_llm_response(content: str) -> MagicMock:
    """Create a mock LLM response."""
    resp = MagicMock()
    resp.content = content
    return resp


# ══════════════════════════════════════════════════════════════════════════════
# _build_followup_message
# ══════════════════════════════════════════════════════════════════════════════


class TestBuildFollowupMessage:
    def test_single_field(self):
        msg = _build_followup_message(["email"])
        assert "e-mail" in msg

    def test_two_fields(self):
        msg = _build_followup_message(["email", "empresa"])
        assert "e-mail" in msg
        assert "empresa" in msg
        assert "e do" in msg

    def test_three_fields(self):
        msg = _build_followup_message(["email", "empresa", "interesse"])
        assert "e-mail" in msg
        assert "empresa" in msg
        assert "interesse" in msg


# ══════════════════════════════════════════════════════════════════════════════
# _extract_batch_fields
# ══════════════════════════════════════════════════════════════════════════════


class TestExtractBatchFields:
    @pytest.mark.asyncio
    async def test_extract_all_fields(self):
        llm_json = json.dumps({
            "email": "joao@test.com",
            "empresa": "Acme Ltda",
            "interesse": "CRM",
        })
        with patch("app.services.chat_service._get_llm") as mock_get_llm:
            mock_llm = AsyncMock()
            mock_llm.ainvoke.return_value = _mock_llm_response(llm_json)
            mock_get_llm.return_value = mock_llm

            result = await _extract_batch_fields(
                LEAD_BATCH_FIELDS, "joao@test.com, Acme Ltda, CRM", "lead"
            )

        assert result["extraidos"]["email"] == "joao@test.com"
        assert result["extraidos"]["empresa"] == "Acme Ltda"
        assert result["extraidos"]["interesse"] == "CRM"
        assert len(result["campos_extraidos"]) == 3
        assert result["campos_faltantes"] == []

    @pytest.mark.asyncio
    async def test_extract_partial_fields(self):
        llm_json = json.dumps({
            "email": "joao@test.com",
            "empresa": "",
            "interesse": "",
        })
        with patch("app.services.chat_service._get_llm") as mock_get_llm:
            mock_llm = AsyncMock()
            mock_llm.ainvoke.return_value = _mock_llm_response(llm_json)
            mock_get_llm.return_value = mock_llm

            result = await _extract_batch_fields(
                LEAD_BATCH_FIELDS, "joao@test.com", "lead"
            )

        assert result["extraidos"]["email"] == "joao@test.com"
        assert result["campos_extraidos"] == ["email"]
        assert result["campos_faltantes"] == ["empresa", "interesse"]

    @pytest.mark.asyncio
    async def test_invalid_email_rejected(self):
        llm_json = json.dumps({
            "email": "invalido",
            "empresa": "Acme",
            "interesse": "CRM",
        })
        with patch("app.services.chat_service._get_llm") as mock_get_llm:
            mock_llm = AsyncMock()
            mock_llm.ainvoke.return_value = _mock_llm_response(llm_json)
            mock_get_llm.return_value = mock_llm

            result = await _extract_batch_fields(
                LEAD_BATCH_FIELDS, "invalido, Acme, CRM", "lead"
            )

        assert "email" not in result["campos_extraidos"]
        assert "email" in result["campos_faltantes"]
        assert result["extraidos"]["empresa"] == "Acme"

    @pytest.mark.asyncio
    async def test_llm_error_returns_empty(self):
        with patch("app.services.chat_service._get_llm") as mock_get_llm:
            mock_llm = AsyncMock()
            mock_llm.ainvoke.side_effect = Exception("API error")
            mock_get_llm.return_value = mock_llm

            result = await _extract_batch_fields(
                LEAD_BATCH_FIELDS, "test", "lead"
            )

        assert result["extraidos"] == {}
        assert result["campos_extraidos"] == []
        assert result["campos_faltantes"] == LEAD_BATCH_FIELDS

    @pytest.mark.asyncio
    async def test_invalid_json_returns_empty(self):
        with patch("app.services.chat_service._get_llm") as mock_get_llm:
            mock_llm = AsyncMock()
            mock_llm.ainvoke.return_value = _mock_llm_response("not json at all")
            mock_get_llm.return_value = mock_llm

            result = await _extract_batch_fields(
                LEAD_BATCH_FIELDS, "test", "lead"
            )

        assert result["extraidos"] == {}
        assert result["campos_faltantes"] == LEAD_BATCH_FIELDS


# ══════════════════════════════════════════════════════════════════════════════
# _processar_fase_nome
# ══════════════════════════════════════════════════════════════════════════════


class TestProcessarFaseNome:
    @pytest.mark.asyncio
    async def test_valid_name_transitions_to_lote(self):
        with patch("app.services.chat_service._get_llm") as mock_get_llm:
            mock_llm = AsyncMock()
            mock_llm.ainvoke.return_value = _mock_llm_response(
                "VALIDO\nPrazer, João! Agora preciso de mais alguns dados."
            )
            mock_get_llm.return_value = mock_llm

            result = await _processar_fase_nome("João", {}, 0, "lead")

        assert result["fase"] == "lote"
        assert result["dados_parciais"]["nome"] == "João"
        assert result["campos_pendentes"] == LEAD_BATCH_FIELDS
        assert "nome" in result["campos_extraidos"]
        assert result["tentativas_falhas"] == 0

    @pytest.mark.asyncio
    async def test_invalid_name_increments_attempts(self):
        with patch("app.services.chat_service._get_llm") as mock_get_llm:
            mock_llm = AsyncMock()
            mock_llm.ainvoke.return_value = _mock_llm_response(
                "INVALIDO\nPode me dizer seu nome completo?"
            )
            mock_get_llm.return_value = mock_llm

            result = await _processar_fase_nome("", {}, 0, "lead")

        assert result["fase"] == "nome"
        assert result["tentativas_falhas"] == 1

    @pytest.mark.asyncio
    async def test_attempt_limit_nome(self):
        result = await _processar_fase_nome("test", {}, 3, "lead")
        assert result["concluido"] is True
        assert result["encerrado_por_falha"] is True
        assert result["mensagem"] == MSG_LIMITE_TENTATIVAS

    @pytest.mark.asyncio
    async def test_llm_error_nome(self):
        with patch("app.services.chat_service._get_llm") as mock_get_llm:
            mock_llm = AsyncMock()
            mock_llm.ainvoke.side_effect = Exception("API error")
            mock_get_llm.return_value = mock_llm

            result = await _processar_fase_nome("João", {}, 0, "lead")

        assert result["fase"] == "nome"
        assert result["tentativas_falhas"] == 0  # technical error, not user fault


# ══════════════════════════════════════════════════════════════════════════════
# _processar_fase_lote
# ══════════════════════════════════════════════════════════════════════════════


class TestProcessarFaseLote:
    @pytest.mark.asyncio
    async def test_all_fields_extracted_completes(self):
        llm_json = json.dumps({
            "email": "joao@test.com",
            "empresa": "Acme",
            "interesse": "CRM",
        })
        with patch("app.services.chat_service._get_llm") as mock_get_llm:
            mock_llm = AsyncMock()
            mock_llm.ainvoke.return_value = _mock_llm_response(llm_json)
            mock_get_llm.return_value = mock_llm

            result = await _processar_fase_lote(
                "joao@test.com, Acme, CRM",
                LEAD_BATCH_FIELDS,
                {"nome": "João"},
                0,
                "lead",
            )

        assert result["concluido"] is True
        assert result["encerrado_por_falha"] is False
        assert result["dados_parciais"]["email"] == "joao@test.com"
        assert result["dados_parciais"]["nome"] == "João"

    @pytest.mark.asyncio
    async def test_partial_extraction_followup(self):
        llm_json = json.dumps({
            "email": "joao@test.com",
            "empresa": "",
            "interesse": "",
        })
        with patch("app.services.chat_service._get_llm") as mock_get_llm:
            mock_llm = AsyncMock()
            mock_llm.ainvoke.return_value = _mock_llm_response(llm_json)
            mock_get_llm.return_value = mock_llm

            result = await _processar_fase_lote(
                "joao@test.com",
                LEAD_BATCH_FIELDS,
                {"nome": "João"},
                0,
                "lead",
            )

        assert result["concluido"] is False
        assert result["tentativas_falhas"] == 0  # progress was made
        assert "empresa" in result["campos_pendentes"]
        assert "email" not in result["campos_pendentes"]

    @pytest.mark.asyncio
    async def test_no_extraction_increments_rounds(self):
        llm_json = json.dumps({
            "email": "",
            "empresa": "",
            "interesse": "",
        })
        with patch("app.services.chat_service._get_llm") as mock_get_llm:
            mock_llm = AsyncMock()
            mock_llm.ainvoke.return_value = _mock_llm_response(llm_json)
            mock_get_llm.return_value = mock_llm

            result = await _processar_fase_lote(
                "qualquer coisa off-topic",
                LEAD_BATCH_FIELDS,
                {"nome": "João"},
                0,
                "lead",
            )

        assert result["concluido"] is False
        assert result["tentativas_falhas"] == 1

    @pytest.mark.asyncio
    async def test_attempt_limit_lote(self):
        result = await _processar_fase_lote(
            "test",
            LEAD_BATCH_FIELDS,
            {"nome": "João"},
            3,
            "lead",
        )
        assert result["concluido"] is True
        assert result["encerrado_por_falha"] is True
        assert result["mensagem"] == MSG_LIMITE_TENTATIVAS


# ══════════════════════════════════════════════════════════════════════════════
# processar_mensagem_bot (integration)
# ══════════════════════════════════════════════════════════════════════════════


class TestProcessarMensagemBot:
    @pytest.mark.asyncio
    async def test_nome_to_lote_transition_lead(self):
        with patch("app.services.chat_service._get_llm") as mock_get_llm:
            mock_llm = AsyncMock()
            mock_llm.ainvoke.return_value = _mock_llm_response(
                "VALIDO\nPrazer, Felipe!"
            )
            mock_get_llm.return_value = mock_llm

            result = await processar_mensagem_bot(
                "Felipe", "nome", [], {}, 0, "lead"
            )

        assert result["fase"] == "lote"
        assert result["dados_parciais"]["nome"] == "Felipe"
        assert result["campos_pendentes"] == LEAD_BATCH_FIELDS

    @pytest.mark.asyncio
    async def test_nome_to_lote_transition_ticket(self):
        with patch("app.services.chat_service._get_llm") as mock_get_llm:
            mock_llm = AsyncMock()
            mock_llm.ainvoke.return_value = _mock_llm_response(
                "VALIDO\nPrazer, Felipe!"
            )
            mock_get_llm.return_value = mock_llm

            result = await processar_mensagem_bot(
                "Felipe", "nome", [], {}, 0, "ticket"
            )

        assert result["fase"] == "lote"
        assert result["campos_pendentes"] == TICKET_BATCH_FIELDS

    @pytest.mark.asyncio
    async def test_ticket_batch_all_fields(self):
        llm_json = json.dumps({
            "empresa": "Acme Ltda",
            "cargo": "Analista de TI",
            "email": "felipe@acme.com",
            "descricao": "meu sistema não abre desde ontem",
        })
        with patch("app.services.chat_service._get_llm") as mock_get_llm:
            mock_llm = AsyncMock()
            mock_llm.ainvoke.return_value = _mock_llm_response(llm_json)
            mock_get_llm.return_value = mock_llm

            result = await processar_mensagem_bot(
                "Acme Ltda, Analista de TI, felipe@acme.com, meu sistema não abre desde ontem",
                "lote",
                TICKET_BATCH_FIELDS,
                {"nome": "Felipe"},
                0,
                "ticket",
            )

        assert result["concluido"] is True
        assert result["dados_parciais"]["empresa"] == "Acme Ltda"
        assert result["dados_parciais"]["cargo"] == "Analista de TI"
        assert result["dados_parciais"]["email"] == "felipe@acme.com"
