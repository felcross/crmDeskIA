from app.services.analytics_service import (
    compute_kpis,
    contacts_by_month,
    deals_by_stage,
    sales_funnel,
    value_by_month,
)


class TestComputeKPIs:
    def test_empty_deals(self):
        result = compute_kpis([])
        assert result["total_deals"] == 0
        assert result["pipeline_value"] == 0.0
        assert result["average_ticket"] == 0.0
        assert result["closed_deals"] == 0

    def test_with_deals(self, mock_deals):
        result = compute_kpis(mock_deals)
        assert result["total_deals"] == 3
        assert result["pipeline_value"] == 30000.0
        assert result["closed_deals"] == 2
        assert result["average_ticket"] == 10000.0


class TestDealsByStage:
    def test_empty(self):
        result = deals_by_stage([])
        assert result.data == []

    def test_grouped(self, mock_deals):
        result = deals_by_stage(mock_deals)
        labels = [d.label for d in result.data]
        assert "closedwon" in labels
        assert "qualifiedtobuy" in labels


class TestSalesFunnel:
    def test_empty(self):
        result = sales_funnel([])
        assert result.data == []

    def test_ordering(self, mock_deals):
        result = sales_funnel(mock_deals)
        assert len(result.data) >= 1


class TestValueByMonth:
    def test_empty(self):
        result = value_by_month([])
        assert result.data == []

    def test_grouping(self, mock_deals):
        result = value_by_month(mock_deals)
        assert len(result.data) >= 1


class TestContactsByMonth:
    def test_empty(self):
        result = contacts_by_month([])
        assert result.data == []

    def test_grouping(self, mock_contacts):
        result = contacts_by_month(mock_contacts)
        assert len(result.data) >= 1
