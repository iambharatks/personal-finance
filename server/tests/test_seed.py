"""Checks the real seed file against totals worked out independently with the csv module.
Skipped when private/seed/transactions.csv is absent (it is never committed)."""

import csv

import pytest

from app.cli import DEFAULT_SEED_CSV
from app.seed import seed_from_csv

pytestmark = pytest.mark.skipif(not DEFAULT_SEED_CSV.exists(), reason="no private seed file")


@pytest.fixture
def seeded(db):
    result = seed_from_csv(db, DEFAULT_SEED_CSV)
    with DEFAULT_SEED_CSV.open(encoding="utf-8-sig", newline="") as handle:
        rows = list(csv.DictReader(handle))
    return result, rows


def _net(rows, *groups):
    return sum(float(r["money_in"]) - float(r["money_out"]) for r in rows if r["group"] in groups)


def test_seed_loads_every_row(client, seeded, db):
    result, rows = seeded
    assert result["rows"] == len(rows) == 1397
    assert result["opening_balance"] == 1.0
    assert len(client.get("/api/categories").json()) == len({r["category"] for r in rows}) == 36
    assert client.get("/api/meta").json() == {
        "min_date": rows[0]["date"],
        "max_date": rows[-1]["date"],
        "txn_count": 1397,
    }
    assert seed_from_csv(db, DEFAULT_SEED_CSV)["skipped"] is True  # loading twice adds nothing


def test_books_reconcile(client, seeded):
    _, rows = seeded
    k = client.get("/api/dashboard").json()

    assert k["income"] == pytest.approx(_net(rows, "Salary", "Other income"), abs=0.01)
    assert k["spending"] == pytest.approx(-_net(rows, "Spending"), abs=0.01)
    assert k["tax"] == pytest.approx(-_net(rows, "Tax"), abs=0.01)
    assert k["investing"] == pytest.approx(-_net(rows, "Investing"), abs=0.01)

    # Opening balance + everything in - everything out = the bank's last printed balance.
    assert k["closing_balance"] == pytest.approx(float(rows[-1]["balance"]), abs=0.01)
    assert k["closing_balance"] == 388446.46

    newest = client.get("/api/transactions", params={"page_size": 1}).json()["items"][0]
    assert newest["balance"] == 388446.46


def test_monthly_flows_add_up_to_the_kpis(client, seeded):
    k = client.get("/api/dashboard").json()
    flows = client.get("/api/charts/monthly-flows").json()
    for key in ("income", "spending", "tax", "investing"):
        assert sum(f[key] for f in flows) == pytest.approx(k[key], abs=0.05)
    assert len(flows) == 36  # Nov 2023 .. Oct 2026, no holes

    spend = client.get("/api/charts/category-spend").json()
    assert sum(r["total"] for r in spend) == pytest.approx(k["spending"], abs=0.05)
