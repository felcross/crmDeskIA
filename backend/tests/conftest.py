import pytest
from unittest.mock import AsyncMock, MagicMock, patch


@pytest.fixture
def mock_deals():
    return [
        {"id": "1", "nome": "Deal A", "valor": 10000.0, "estagio": "closedwon", "pipeline": "default", "data_close": "2025-01-15", "criado_em": "2025-01-01"},
        {"id": "2", "nome": "Deal B", "valor": 5000.0, "estagio": "qualifiedtobuy", "pipeline": "default", "data_close": "2025-02-15", "criado_em": "2025-01-15"},
        {"id": "3", "nome": "Deal C", "valor": 15000.0, "estagio": "closedwon", "pipeline": "default", "data_close": "2025-03-15", "criado_em": "2025-02-01"},
    ]


@pytest.fixture
def mock_contacts():
    return [
        {"id": "1", "nome": "João Silva", "email": "joao@test.com", "telefone": "+5511999999999", "status_lead": "NEW", "criado_em": "2025-01-01"},
        {"id": "2", "nome": "Maria Santos", "email": "maria@test.com", "telefone": "+5511888888888", "status_lead": "CONTACTED", "criado_em": "2025-01-15"},
    ]
