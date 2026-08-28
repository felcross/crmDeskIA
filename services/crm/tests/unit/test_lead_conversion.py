"""Tests for POST /api/v1/leads/{id}/convert endpoint."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException


@pytest.fixture
def mock_lead():
    lead = MagicMock()
    lead.id = 1
    lead.nome = "João Silva"
    lead.email = "joao@test.com"
    return lead


@pytest.fixture
def mock_deal():
    deal = MagicMock()
    deal.id = 10
    deal.nome = "João Silva"
    deal.valor = 5000.0
    deal.estagio = "Prospecção"
    deal.pipeline = "default"
    deal.data_close = None
    deal.criado_em = "2026-08-26T10:00:00"
    return deal


@pytest.mark.asyncio
async def test_convert_lead_success(mock_lead, mock_deal):
    """Converting a valid lead creates a deal and returns it."""
    from app.api.v1.leads import convert_lead
    from app.models.lead import ConvertLeadRequest

    mock_db = AsyncMock()
    mock_lead_repo = AsyncMock()
    mock_deal_repo = AsyncMock()

    mock_lead_repo.get_by_id.return_value = mock_lead
    mock_deal_repo.get_by_lead_id.return_value = None
    mock_deal_repo.create_deal.return_value = mock_deal

    with (
        patch("app.api.v1.leads.LeadRepository", return_value=mock_lead_repo),
        patch("app.api.v1.leads.DealRepository", return_value=mock_deal_repo),
    ):
        request = ConvertLeadRequest(valor=5000.0)
        response = await convert_lead(lead_id=1, request=request, db=mock_db)

    assert response.data.nome == "João Silva"
    assert response.data.valor == 5000.0
    mock_deal_repo.create_deal.assert_called_once()
    mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_convert_lead_not_found():
    """Converting a non-existent lead returns 404."""
    from app.api.v1.leads import convert_lead
    from app.models.lead import ConvertLeadRequest

    mock_db = AsyncMock()
    mock_lead_repo = AsyncMock()
    mock_lead_repo.get_by_id.return_value = None

    with patch("app.api.v1.leads.LeadRepository", return_value=mock_lead_repo):
        request = ConvertLeadRequest(valor=5000.0)
        with pytest.raises(HTTPException) as exc_info:
            await convert_lead(lead_id=999, request=request, db=mock_db)
        assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_convert_lead_already_converted(mock_lead, mock_deal):
    """Converting a lead that already has a deal returns 409."""
    from app.api.v1.leads import convert_lead
    from app.models.lead import ConvertLeadRequest

    mock_db = AsyncMock()
    mock_lead_repo = AsyncMock()
    mock_deal_repo = AsyncMock()

    mock_lead_repo.get_by_id.return_value = mock_lead
    mock_deal_repo.get_by_lead_id.return_value = mock_deal

    with (
        patch("app.api.v1.leads.LeadRepository", return_value=mock_lead_repo),
        patch("app.api.v1.leads.DealRepository", return_value=mock_deal_repo),
    ):
        request = ConvertLeadRequest(valor=5000.0)
        with pytest.raises(HTTPException) as exc_info:
            await convert_lead(lead_id=1, request=request, db=mock_db)
        assert exc_info.value.status_code == 409
