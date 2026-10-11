import os
import tempfile
from datetime import date
from pathlib import Path

# Point the app at a throwaway database before anything imports it.
_TMP = Path(tempfile.mkdtemp(prefix="finance-tests-"))
os.environ["DATABASE_URL"] = f"sqlite:///{(_TMP / 'test.db').as_posix()}"
os.environ["APP_ENV"] = "development"
os.environ["APP_PASSWORD_HASH"] = ""
os.environ["SESSION_SECRET"] = ""
os.environ.pop("VERCEL", None)

import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy.orm import Session  # noqa: E402

from app.config import SERVER_DIR, get_settings  # noqa: E402
from app.db import get_engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models import Account, Base, Category, Group, Transaction  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def schema():
    # Built by the real migrations, so they are exercised on every run.
    command.upgrade(Config(str(SERVER_DIR / "alembic.ini")), "head")


@pytest.fixture
def db():
    with Session(get_engine(), expire_on_commit=False) as session:
        yield session
        session.rollback()
        for table in reversed(Base.metadata.sorted_tables):
            session.execute(table.delete())
        session.commit()


@pytest.fixture
def client(db):
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def with_password():
    """Turn the login on for one test."""
    from app.auth import hash_password

    settings = get_settings()
    settings.app_password_hash = hash_password("correct horse battery")
    settings.session_secret = "s" * 40
    yield "correct horse battery"
    settings.app_password_hash = ""
    settings.session_secret = ""


# (date, category, money_in, money_out, payee)
LEDGER = [
    ("2025-04-01", "Salary", 50000, 0, "Employer"),
    ("2025-04-03", "Rent", 0, 10000, "Landlord"),
    ("2025-04-05", "Groceries", 0, 2000, "Big Bazaar"),
    ("2025-04-06", "Groceries", 500, 0, "Big Bazaar"),  # refund nets against spending
    ("2025-04-10", "SIP", 0, 5000, "Fund house"),
    ("2025-04-12", "Stock sale", 1000, 0, "Broker"),  # nets against investing
    ("2025-04-15", "To own account", 0, 3000, "Self"),
    ("2025-04-20", "Reversed", 0, 700, "Shop"),
    ("2025-04-20", "Reversed", 700, 0, "Shop"),
    ("2025-05-01", "Salary", 50000, 0, "Employer"),
    ("2025-05-02", "Income tax", 0, 4000, "CBDT"),
    ("2025-05-03", "Small UPI", 0, 300, "Chai stall"),
    # No June rows on purpose: a quiet month.
    ("2025-07-01", "Rent", 0, 10000, "Landlord"),
]

_CATEGORIES = {
    # name: (group, kind, is_fallback)
    "Salary": ("Salary", "income", False),
    "Rent": ("Spending", "expense", False),
    "Groceries": ("Spending", "expense", False),
    "Small UPI": ("Spending", "expense", True),
    "Income tax": ("Tax", "tax", False),
    "SIP": ("Investing", "invest", False),
    "Stock sale": ("Investing", "invest", False),
    "To own account": ("Own accounts", "transfer", False),
    "Reversed": ("Reversed", "neutral", False),
}


@pytest.fixture
def ledger(db):
    """One account opening at 1,000 with the LEDGER rows above.

    All time: income 100,000 · spending 21,800 · tax 4,000 · investing 4,000 ·
    net savings 74,200 · closing balance 68,200.
    """
    account = Account(name="Test Savings", type="savings", bank="Test", opening_balance=1000)
    db.add(account)
    groups: dict[str, Group] = {}
    categories: dict[str, Category] = {}
    for name, (group_name, kind, is_fallback) in _CATEGORIES.items():
        if group_name not in groups:
            groups[group_name] = Group(name=group_name, kind=kind, sort=len(groups) + 1)
            db.add(groups[group_name])
            db.flush()
        categories[name] = Category(
            name=name, group_id=groups[group_name].id, is_fallback=is_fallback
        )
        db.add(categories[name])
    db.flush()
    for seq, (day, category, money_in, money_out, payee) in enumerate(LEDGER):
        db.add(
            Transaction(
                account_id=account.id,
                date=date.fromisoformat(day),
                seq=seq,
                month=day[:7],
                category_id=categories[category].id,
                category_source="seed",
                payee=payee,
                money_in=money_in,
                money_out=money_out,
            )
        )
    db.commit()
    return {"account": account, "categories": categories, "groups": groups}
