"""Load the curated transactions CSV (date, month, period, group, category, payee, note,
money_in, money_out, balance) into one account as a single import batch."""

import csv
import hashlib
import io
from collections import Counter
from datetime import date
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Account, Category, Group, ImportBatch, Transaction

# (name, kind) in display order. See services/metrics.py for what each kind means.
GROUPS = [
    ("Salary", "income"),
    ("Other income", "income"),
    ("Spending", "expense"),
    ("Tax", "tax"),
    ("Investing", "invest"),
    ("Own accounts", "transfer"),
    ("Cash", "neutral"),
    ("Friends & others", "neutral"),
    ("Reversed", "neutral"),
]

# name -> (icon, is_essential). Categories missing here are still created, without either.
CATEGORY_META: dict[str, tuple[str, bool | None]] = {
    "Salary": ("💼", None),
    "Savings interest": ("🏦", None),
    "Dividends": ("💹", None),
    "Employer credits (non-salary)": ("🧾", None),
    "Refunds & cashback": ("↩️", None),
    "Rent": ("🏠", True),
    "Groceries & household": ("🛒", True),
    "Food & dining out": ("🍽️", False),
    "Travel & commute": ("✈️", False),
    "Fuel & vehicle": ("⛽", True),
    "Shopping & personal": ("🛍️", False),
    "Bills, recharges & utilities": ("💡", True),
    "Health & medical": ("🩺", True),
    "Fitness & nutrition": ("🏋️", False),
    "Subscriptions": ("🔁", False),
    "Learning & career": ("🎓", False),
    "Home & appliances": ("🛋️", False),
    "Entertainment": ("🎬", False),
    "Gifts": ("🎁", False),
    "Shared costs (Splitwise)": ("🤝", False),
    "Credit card bills": ("💳", None),
    "Bank & broker charges": ("🏛️", None),
    "Other payments ≥₹2k (unlabelled)": ("❓", None),
    "Small everyday UPI (unlabelled)": ("❔", None),
    "MF SIPs (ICICI Direct)": ("📈", None),
    "MF SIPs (Groww)": ("🌱", None),
    "Stocks & IPOs (ICICI Direct)": ("📊", None),
    "Stock sales & settlements": ("💰", None),
    "To your other accounts": ("➡️", None),
    "From your other accounts": ("⬅️", None),
    "Cash withdrawal": ("🏧", None),
    "Income tax & govt fees": ("🧮", None),
    "Lent to a friend": ("🫱", None),
    "Repaid friends": ("🫲", None),
    "Received from friends/others": ("🙌", None),
    "Reversed payment": ("🔄", None),
}


def _dedupe_keys(account_id: int, rows: list[dict]) -> list[str]:
    """Stable identity per row: what the bank printed, plus a counter for exact twins."""
    seen: Counter[str] = Counter()
    keys = []
    for row in rows:
        base = "|".join(
            [
                str(account_id),
                row["date"],
                f"{float(row['money_in']):.2f}",
                f"{float(row['money_out']):.2f}",
                f"{float(row['balance']):.2f}",
            ]
        )
        seen[base] += 1
        keys.append(hashlib.sha256(f"{base}|{seen[base]}".encode()).hexdigest())
    return keys


def seed_from_csv(db: Session, csv_path: Path, account_name: str = "ICICI Savings") -> dict:
    raw = csv_path.read_bytes()
    file_hash = hashlib.sha256(raw).hexdigest()
    rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
    if not rows:
        raise ValueError(f"{csv_path} has no rows")

    account = db.scalar(select(Account).where(Account.name == account_name))
    if account is None:
        account = Account(name=account_name, type="savings", bank="ICICI")
        db.add(account)
        db.flush()

    already = db.scalar(
        select(ImportBatch.id).where(
            ImportBatch.account_id == account.id, ImportBatch.file_sha256 == file_hash
        )
    )
    if already:
        return {"skipped": True, "reason": "this file is already imported", "rows": 0}

    groups = {g.name: g for g in db.scalars(select(Group))}
    for sort, (name, kind) in enumerate(GROUPS, start=1):
        if name not in groups:
            groups[name] = Group(name=name, kind=kind, sort=sort)
            db.add(groups[name])
    for name in dict.fromkeys(row["group"] for row in rows):
        if name not in groups:
            groups[name] = Group(name=name, kind="neutral", sort=len(groups) + 1)
            db.add(groups[name])
    db.flush()

    categories = {c.name: c for c in db.scalars(select(Category))}
    for row in rows:
        name = row["category"]
        if name not in categories:
            icon, is_essential = CATEGORY_META.get(name, (None, None))
            categories[name] = Category(
                name=name,
                group_id=groups[row["group"]].id,
                icon=icon,
                is_essential=is_essential,
                is_fallback=name.endswith("(unlabelled)"),
            )
            db.add(categories[name])
    db.flush()

    has_history = db.scalar(
        select(func.count()).select_from(Transaction).where(Transaction.account_id == account.id)
    )
    if not has_history:
        first = rows[0]
        account.opening_balance = round(
            float(first["balance"]) - float(first["money_in"]) + float(first["money_out"]), 2
        )

    batch = ImportBatch(
        account_id=account.id,
        filename=csv_path.name,
        format="curated_csv",
        file_sha256=file_hash,
        row_count=len(rows),
    )
    db.add(batch)
    db.flush()

    keys = _dedupe_keys(account.id, rows)
    db.add_all(
        Transaction(
            account_id=account.id,
            date=date.fromisoformat(row["date"]),
            seq=seq,
            month=row["date"][:7],
            category_id=categories[row["category"]].id,
            category_source="seed",
            payee=row["payee"].strip(),
            note=row["note"].strip(),
            money_in=float(row["money_in"]),
            money_out=float(row["money_out"]),
            statement_balance=float(row["balance"]),
            import_batch_id=batch.id,
            dedupe_key=key,
        )
        for seq, (row, key) in enumerate(zip(rows, keys, strict=True))
    )
    db.commit()
    return {
        "skipped": False,
        "rows": len(rows),
        "account": account.name,
        "categories": len(categories),
        "opening_balance": account.opening_balance,
    }
