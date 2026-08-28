"""Tests for bug fixes and unified atendimento flow."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import status

# ══════════════════════════════════════════════════════════════════════════════
# T1: OAuth callback redirect
# ══════════════════════════════════════════════════════════════════════════════


class TestOAuthCallbackRedirect:
    """Verify callback returns 302 redirect instead of 204."""

    @pytest.mark.asyncio
    async def test_callback_missing_code_redirects_to_login_error(self):
        """Missing code should redirect to /login?error=auth_failed."""
        from fastapi.testclient import TestClient

        from app.main import app

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get("/api/v1/auth/callback", follow_redirects=False)
        assert resp.status_code == status.HTTP_302_FOUND
        assert "/login?error=" in resp.headers.get("location", "")

    @pytest.mark.asyncio
    async def test_callback_invalid_state_redirects_to_login_error(self):
        """Invalid OAuth state should redirect to /login?error=auth_failed."""
        from fastapi.testclient import TestClient

        from app.main import app

        client = TestClient(app, raise_server_exceptions=False)
        resp = client.get(
            "/api/v1/auth/callback?code=test&state=bad",
            cookies={"oauth_state": "different-state"},
            follow_redirects=False,
        )
        assert resp.status_code == status.HTTP_302_FOUND
        assert "/login?error=" in resp.headers.get("location", "")

    def test_google_auth_url_no_offline_consent(self):
        """Auth URL should NOT contain access_type=offline or prompt=consent."""
        from app.auth.google_oauth import get_google_auth_url

        url = get_google_auth_url(state="test")
        assert "access_type=offline" not in url
        assert "prompt=consent" not in url
        assert "response_type=code" in url
        assert "scope=openid" in url


# ══════════════════════════════════════════════════════════════════════════════
# T3: Cache fallback for exchange rates
# ══════════════════════════════════════════════════════════════════════════════


class TestMarketCacheFallback:
    """Verify stale cache is served when AwesomeAPI fails."""

    @pytest.mark.asyncio
    async def test_stale_cache_served_on_api_failure(self):
        """When API fails and stale cache exists, return stale data."""
        from app.services.market_service import AwesomeAPIService

        stale_data = [{"code": "USD", "bid": 5.0, "ask": 5.1}]

        service = AwesomeAPIService()
        service._client = MagicMock()

        with (
            patch("app.services.market_service.redis_cache") as mock_redis,
            patch.object(service, "_get", side_effect=Exception("429 Too Many Requests")),
        ):
            # First call (fresh cache) returns None
            # Second call (stale cache) returns stale data
            mock_redis.get = AsyncMock(side_effect=[None, stale_data])

            result = await service.get_last_quotes("USD-BRL")

        assert result == stale_data

    @pytest.mark.asyncio
    async def test_api_failure_no_cache_raises(self):
        """When API fails and no cache exists, exception should propagate."""
        from app.services.market_service import AwesomeAPIService

        service = AwesomeAPIService()
        service._client = MagicMock()

        with (
            patch("app.services.market_service.redis_cache") as mock_redis,
            patch.object(service, "_get", side_effect=Exception("429")),
        ):
            mock_redis.get = AsyncMock(return_value=None)

            with pytest.raises(Exception, match="429"):
                await service.get_last_quotes("USD-BRL")

    @pytest.mark.asyncio
    async def test_cache_ttl_is_10_minutes(self):
        """CACHE_TTL should be 10 minutes (600 seconds)."""
        from app.services.market_service import CACHE_TTL

        assert CACHE_TTL == 10 * 60

    @pytest.mark.asyncio
    async def test_stale_ttl_is_1_hour(self):
        """STALE_TTL should be 1 hour (3600 seconds)."""
        from app.services.market_service import STALE_TTL

        assert STALE_TTL == 60 * 60


# ══════════════════════════════════════════════════════════════════════════════
# T7: Unified atendimento flow
# ══════════════════════════════════════════════════════════════════════════════


class TestUnifiedAtendimentoFlow:
    """Verify sequential ticket flow creates lead + ticket."""

    @pytest.mark.asyncio
    async def test_extract_single_field_valid(self):
        """Valid name should be extracted successfully."""
        from app.services.chat_service import _extract_single_field

        with patch("app.services.chat_service._get_llm") as mock_llm:
            mock_response = MagicMock()
            mock_response.content = "João Silva"
            mock_llm.return_value.ainvoke = AsyncMock(return_value=mock_response)

            result = await _extract_single_field("nome", "Meu nome é João Silva", "ticket")

        assert result == "João Silva"

    @pytest.mark.asyncio
    async def test_extract_single_field_invalid(self):
        """Invalid response should return None."""
        from app.services.chat_service import _extract_single_field

        with patch("app.services.chat_service._get_llm") as mock_llm:
            mock_response = MagicMock()
            mock_response.content = "INVALIDO"
            mock_llm.return_value.ainvoke = AsyncMock(return_value=mock_response)

            result = await _extract_single_field("email", "não sei", "ticket")

        assert result is None

    @pytest.mark.asyncio
    async def test_extract_email_validation(self):
        """Invalid email format should return None."""
        from app.services.chat_service import _extract_single_field

        with patch("app.services.chat_service._get_llm") as mock_llm:
            mock_response = MagicMock()
            mock_response.content = "not-an-email"
            mock_llm.return_value.ainvoke = AsyncMock(return_value=mock_response)

            result = await _extract_single_field("email", "not-an-email", "ticket")

        assert result is None

    @pytest.mark.asyncio
    async def test_ticket_flow_sequential_phases(self):
        """Ticket flow should progress through phases: nome→empresa→cargo→email→descricao."""
        from app.services.chat_service import processar_ticket

        with patch("app.services.chat_service._extract_single_field") as mock_extract:
            mock_extract.return_value = "João Silva"

            result = await processar_ticket(
                mensagem="João Silva",
                fase="nome",
                campos_pendentes=[],
                dados_parciais={},
                tentativas_falhas=0,
            )

        assert result["concluido"] is False
        assert result["fase"] == "empresa"
        assert result["dados_parciais"]["nome"] == "João Silva"
        assert "Qual o" in result["mensagem"]

    @pytest.mark.asyncio
    async def test_ticket_flow_completion_creates_lead_and_ticket(self):
        """When all fields collected, should create lead + ticket."""
        from app.services.chat_service import processar_ticket

        dados_parciais = {
            "nome": "João Silva",
            "empresa": "Acme Corp",
            "cargo": "Gerente",
            "email": "joao@acme.com",
        }

        mock_lead = MagicMock()
        mock_lead.id = 1
        mock_lead.email = "joao@acme.com"

        mock_company = MagicMock()
        mock_company.id = 1

        mock_ticket = MagicMock()
        mock_ticket.id = 1
        mock_ticket.nome = "João Silva"
        mock_ticket.email = "joao@acme.com"
        mock_ticket.descricao = "Preciso de ajuda"
        mock_ticket.prioridade = "media"
        mock_ticket.status = "aberto"
        mock_ticket.cargo = "Gerente"
        mock_ticket.company_id = 1
        mock_ticket.created_at = "2025-01-01"

        mock_session = AsyncMock()

        async def fake_get_db():
            yield mock_session

        with (
            patch("app.services.chat_service._extract_single_field") as mock_extract,
            patch("app.dependencies.get_db", side_effect=fake_get_db),
        ):
            mock_extract.return_value = "Preciso de ajuda"

            with (
                patch("app.repositories.lead_repo.LeadRepository") as mock_lead_repo_cls,
                patch("app.repositories.company_repo.CompanyRepository") as mock_company_repo_cls,
                patch("app.repositories.ticket_repo.TicketRepository") as mock_ticket_repo_cls,
            ):
                mock_lead_repo = AsyncMock()
                mock_lead_repo.get_by_email = AsyncMock(return_value=mock_lead)
                mock_lead_repo_cls.return_value = mock_lead_repo

                mock_company_repo = AsyncMock()
                mock_company_repo.get_by_nome_case_insensitive = AsyncMock(
                    return_value=mock_company
                )
                mock_company_repo_cls.return_value = mock_company_repo

                mock_ticket_repo = AsyncMock()
                mock_ticket_repo.create_ticket = AsyncMock(
                    return_value=mock_ticket
                )
                mock_ticket_repo_cls.return_value = mock_ticket_repo

                result = await processar_ticket(
                    mensagem="Preciso de ajuda",
                    fase="descricao",
                    campos_pendentes=[],
                    dados_parciais=dados_parciais,
                    tentativas_falhas=0,
                )

        assert result["concluido"] is True
        assert result["encerrado_por_falha"] is False
        assert result["resultado"]["lead_id"] == 1
        mock_ticket_repo.create_ticket.assert_called_once()
        call_kwargs = mock_ticket_repo.create_ticket.call_args[1]
        assert call_kwargs["lead_id"] == 1

    @pytest.mark.asyncio
    async def test_ticket_flow_creates_new_lead_if_not_exists(self):
        """When lead doesn't exist by email, should create new lead."""
        from app.services.chat_service import processar_ticket

        dados_parciais = {
            "nome": "Nova Pessoa",
            "empresa": "Nova Corp",
            "cargo": "Analista",
            "email": "nova@corp.com",
        }

        mock_new_lead = MagicMock()
        mock_new_lead.id = 99
        mock_new_lead.email = "nova@corp.com"

        mock_company = MagicMock()
        mock_company.id = 1

        mock_ticket = MagicMock()
        mock_ticket.id = 1
        mock_ticket.nome = "Nova Pessoa"
        mock_ticket.email = "nova@corp.com"
        mock_ticket.descricao = "Teste"
        mock_ticket.prioridade = "media"
        mock_ticket.status = "aberto"
        mock_ticket.cargo = "Analista"
        mock_ticket.company_id = 1
        mock_ticket.created_at = "2025-01-01"

        mock_session = AsyncMock()

        async def fake_get_db():
            yield mock_session

        with (
            patch("app.services.chat_service._extract_single_field") as mock_extract,
            patch("app.dependencies.get_db", side_effect=fake_get_db),
        ):
            mock_extract.return_value = "Teste"

            with (
                patch("app.repositories.lead_repo.LeadRepository") as mock_lead_repo_cls,
                patch("app.repositories.company_repo.CompanyRepository") as mock_company_repo_cls,
                patch("app.repositories.ticket_repo.TicketRepository") as mock_ticket_repo_cls,
            ):
                mock_lead_repo = AsyncMock()
                mock_lead_repo.get_by_email = AsyncMock(return_value=None)
                mock_lead_repo.create_lead = AsyncMock(return_value=mock_new_lead)
                mock_lead_repo_cls.return_value = mock_lead_repo

                mock_company_repo = AsyncMock()
                mock_company_repo.get_by_nome_case_insensitive = AsyncMock(
                    return_value=mock_company
                )
                mock_company_repo_cls.return_value = mock_company_repo

                mock_ticket_repo = AsyncMock()
                mock_ticket_repo.create_ticket = AsyncMock(
                    return_value=mock_ticket
                )
                mock_ticket_repo_cls.return_value = mock_ticket_repo

                result = await processar_ticket(
                    mensagem="Teste",
                    fase="descricao",
                    campos_pendentes=[],
                    dados_parciais=dados_parciais,
                    tentativas_falhas=0,
                )

        assert result["concluido"] is True
        mock_lead_repo.create_lead.assert_called_once()
        call_kwargs = mock_lead_repo.create_lead.call_args[1]
        assert call_kwargs["email"] == "nova@corp.com"
        assert call_kwargs["status_lead"] == "novo"

    @pytest.mark.asyncio
    async def test_ticket_flow_attempt_limit(self):
        """After 3 failed attempts, flow should terminate."""
        from app.services.chat_service import processar_ticket

        result = await processar_ticket(
            mensagem="xxx",
            fase="nome",
            campos_pendentes=[],
            dados_parciais={},
            tentativas_falhas=3,
        )

        assert result["concluido"] is True
        assert result["encerrado_por_falha"] is True
