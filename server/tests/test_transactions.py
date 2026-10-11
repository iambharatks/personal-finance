def test_list_newest_first_with_running_balance(client, ledger):
    page = client.get("/api/transactions").json()
    assert page["total"] == 13
    assert page["sum_in"] == 102200
    assert page["sum_out"] == 35000
    newest, oldest = page["items"][0], page["items"][-1]
    assert (newest["date"], newest["balance"]) == ("2025-07-01", 68200)
    assert (oldest["date"], oldest["balance"]) == ("2025-04-01", 51000)
    assert newest["category"] == "Rent" and newest["kind"] == "expense"


def test_running_balance_ignores_filter_and_sort(client, ledger):
    page = client.get(
        "/api/transactions", params={"q": "landlord", "sort": "amount", "order": "asc"}
    ).json()
    assert page["total"] == 2
    assert {item["balance"] for item in page["items"]} == {41000, 68200}


def test_same_day_rows_keep_statement_order(client, ledger):
    page = client.get(
        "/api/transactions", params={"from": "2025-04-20", "to": "2025-04-20", "order": "asc"}
    ).json()
    assert [(i["money_out"], i["money_in"], i["balance"]) for i in page["items"]] == [
        (700, 0, 31800),
        (0, 700, 32500),
    ]


def test_filters(client, ledger):
    def count(**params):
        return client.get("/api/transactions", params=params).json()["total"]

    categories = ledger["categories"]
    assert count(unlabelled=True) == 1
    assert count(dir="in") == 5
    assert count(dir="out") == 8
    assert count(min=5000, max=10000) == 3
    assert count(category=categories["Groceries"].id) == 2
    assert count(category=[categories["Groceries"].id, categories["Rent"].id]) == 4
    assert count(group=ledger["groups"]["Spending"].id) == 5
    assert count(account=ledger["account"].id) == 13
    assert count(account=999) == 0
    assert count(q="BAZAAR") == 2
    assert count(q="100%") == 0  # wildcard characters are matched literally


def test_paging(client, ledger):
    first = client.get("/api/transactions", params={"page_size": 5}).json()
    third = client.get("/api/transactions", params={"page_size": 5, "page": 3}).json()
    assert len(first["items"]) == 5 and len(third["items"]) == 3
    ids = {i["id"] for i in first["items"]} | {i["id"] for i in third["items"]}
    assert len(ids) == 8


def test_edit_marks_category_as_manual(client, ledger):
    txn = client.get("/api/transactions", params={"unlabelled": True}).json()["items"][0]
    assert txn["category_source"] == "seed"
    groceries = ledger["categories"]["Groceries"].id

    updated = client.patch(
        f"/api/transactions/{txn['id']}",
        json={"category_id": groceries, "payee": "  Tea shop ", "note": "evening"},
    ).json()
    assert updated["category"] == "Groceries"
    assert updated["category_source"] == "manual"
    assert updated["payee"] == "Tea shop"
    assert updated["note"] == "evening"
    assert updated["balance"] == txn["balance"]

    # The dashboard reads the same rows, so the change shows up there at once.
    spend = {r["name"]: r["total"] for r in client.get("/api/charts/category-spend").json()}
    assert spend == {"Rent": 20000, "Groceries": 1800}


def test_edit_payee_only_keeps_category_source(client, ledger):
    txn = client.get("/api/transactions").json()["items"][0]
    updated = client.patch(f"/api/transactions/{txn['id']}", json={"payee": "New name"}).json()
    assert updated["category_source"] == "seed"


def test_edit_rejects_unknown_ids(client, ledger):
    txn = client.get("/api/transactions").json()["items"][0]
    assert client.patch("/api/transactions/999999", json={"note": "x"}).status_code == 404
    assert (
        client.patch(f"/api/transactions/{txn['id']}", json={"category_id": 999999}).status_code
        == 422
    )


def test_reference_lists(client, ledger):
    accounts = client.get("/api/accounts").json()
    assert accounts[0]["balance"] == 68200 and accounts[0]["txn_count"] == 13
    assert accounts[0]["last_txn_date"] == "2025-07-01"

    categories = client.get("/api/categories").json()
    assert len(categories) == 9
    assert categories[0]["group"] == {
        "id": ledger["groups"]["Salary"].id,
        "name": "Salary",
        "kind": "income",
    }

    meta = client.get("/api/meta").json()
    assert meta == {"min_date": "2025-04-01", "max_date": "2025-07-01", "txn_count": 13}
