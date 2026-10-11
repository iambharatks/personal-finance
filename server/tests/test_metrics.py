import pytest


def test_kpis_all_time(client, ledger):
    k = client.get("/api/dashboard").json()
    assert k["income"] == 100000
    assert k["spending"] == 21800  # refund netted; transfer, reversal, tax, SIP excluded
    assert k["tax"] == 4000
    assert k["investing"] == 4000  # 5,000 bought - 1,000 sold
    assert k["net_savings"] == 74200
    assert k["savings_rate"] == pytest.approx(0.742)
    assert k["invest_rate"] == pytest.approx(0.04)
    assert k["months"] == 3  # April, May, July
    assert k["avg_monthly_spend"] == pytest.approx(21800 / 3, abs=0.01)
    assert k["closing_balance"] == 68200
    assert k["txn_count"] == 13


def test_kpis_respect_date_range(client, ledger):
    k = client.get("/api/dashboard", params={"from": "2025-05-01", "to": "2025-05-31"}).json()
    assert k["income"] == 50000
    assert k["spending"] == 300
    assert k["tax"] == 4000
    assert k["net_savings"] == 45700
    # Closing balance is the balance on the last day, not just this month's movement.
    assert k["closing_balance"] == 78200


def test_kpis_with_no_data(client):
    k = client.get("/api/dashboard").json()
    assert k["income"] == 0
    assert k["savings_rate"] is None
    assert k["runway_months"] is None
    assert k["closing_balance"] == 0


def test_monthly_flows_fill_quiet_months(client, ledger):
    flows = client.get("/api/charts/monthly-flows").json()
    assert [f["month"] for f in flows] == ["2025-04", "2025-05", "2025-06", "2025-07"]
    april, may, june, july = flows
    assert april == {
        "month": "2025-04",
        "income": 50000,
        "spending": 11500,
        "tax": 0,
        "investing": 4000,
        "net_savings": 38500,
    }
    assert may["tax"] == 4000 and may["net_savings"] == 45700
    assert june["income"] == 0 and june["spending"] == 0
    assert july["spending"] == 10000 and july["net_savings"] == -10000


def test_balance_series_is_cumulative(client, ledger):
    points = client.get("/api/charts/balance").json()
    assert points[0] == {"date": "2025-04-01", "balance": 51000}
    assert points[-1] == {"date": "2025-07-01", "balance": 68200}
    # The reversal day nets to zero and still gets one point.
    assert sum(p["date"] == "2025-04-20" for p in points) == 1


def test_balance_series_carries_balance_into_the_period(client, ledger):
    points = client.get("/api/charts/balance", params={"from": "2025-04-25"}).json()
    assert points[0] == {"date": "2025-04-25", "balance": 32500}
    assert points[1] == {"date": "2025-05-01", "balance": 82500}


def test_category_spend_only_counts_expenses(client, ledger):
    rows = client.get("/api/charts/category-spend").json()
    assert [(r["name"], r["total"], r["count"]) for r in rows] == [
        ("Rent", 20000, 2),
        ("Groceries", 1500, 2),
        ("Small UPI", 300, 1),
    ]
    assert sum(r["share"] for r in rows) == pytest.approx(1)
    assert rows[2]["is_fallback"] is True
