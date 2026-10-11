"""The single definition of every headline number.

A group's `kind` decides how its transactions count:

    income    money earned              -> income      (in - out)
    expense   money spent               -> spending    (out - in)
    tax       income tax and govt fees  -> tax         (out - in)
    invest    money moved into assets   -> investing   (out - in, so sales net off)
    transfer  between own accounts      -> ignored
    neutral   cash, friends, reversals  -> ignored

    net savings  = income - spending - tax
    savings rate = net savings / income

Nothing else in the codebase may re-derive these.
"""

from collections import defaultdict
from datetime import date

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.filters import Filters, apply_filters, txn_select
from app.models import Account, Category, Group, Transaction

_SUM_IN = func.coalesce(func.sum(Transaction.money_in), 0)
_SUM_OUT = func.coalesce(func.sum(Transaction.money_out), 0)


def r2(value: float) -> float:
    return round(value + 0.0, 2)  # + 0.0 turns -0.0 into 0.0


def _flows(sums: dict[str, tuple[float, float]]) -> dict[str, float]:
    """Turn {kind: (in, out)} into the four flows plus net savings."""

    def net_in(kind: str) -> float:
        money_in, money_out = sums.get(kind, (0.0, 0.0))
        return money_in - money_out

    income = net_in("income")
    spending = -net_in("expense")
    tax = -net_in("tax")
    investing = -net_in("invest")
    return {
        "income": r2(income),
        "spending": r2(spending),
        "tax": r2(tax),
        "investing": r2(investing),
        "net_savings": r2(income - spending - tax),
    }


def closing_balance(db: Session, f: Filters) -> float:
    """Balance at the end of the period. Only the account and end-date filters apply."""
    accounts = select(func.coalesce(func.sum(Account.opening_balance), 0))
    moved = select(_SUM_IN - _SUM_OUT)
    if f.accounts:
        accounts = accounts.where(Account.id.in_(f.accounts))
        moved = moved.where(Transaction.account_id.in_(f.accounts))
    if f.date_to:
        moved = moved.where(Transaction.date <= f.date_to)
    return r2(float(db.scalar(accounts) or 0) + float(db.scalar(moved) or 0))


def kpis(db: Session, f: Filters) -> dict:
    rows = db.execute(
        apply_filters(txn_select(Group.kind, _SUM_IN, _SUM_OUT, func.count()), f).group_by(
            Group.kind
        )
    ).all()
    flows = _flows(
        {kind: (float(money_in), float(money_out)) for kind, money_in, money_out, _ in rows}
    )
    months = (
        db.scalar(apply_filters(txn_select(func.count(func.distinct(Transaction.month))), f)) or 0
    )
    income, spending = flows["income"], flows["spending"]
    avg_spend = spending / months if months else 0.0
    balance = closing_balance(db, f)
    return {
        **flows,
        "savings_rate": flows["net_savings"] / income if income > 0 else None,
        "invest_rate": flows["investing"] / income if income > 0 else None,
        "months": months,
        "avg_monthly_spend": r2(avg_spend),
        "runway_months": round(balance / avg_spend, 1) if avg_spend > 0 else None,
        "closing_balance": balance,
        "txn_count": sum(count for *_, count in rows),
    }


def balance_series(db: Session, f: Filters) -> list[dict]:
    """End-of-day balance across the selected accounts, one point per day with activity."""
    opening = select(func.coalesce(func.sum(Account.opening_balance), 0))
    daily = select(Transaction.date, _SUM_IN - _SUM_OUT).group_by(Transaction.date)
    if f.accounts:
        opening = opening.where(Account.id.in_(f.accounts))
        daily = daily.where(Transaction.account_id.in_(f.accounts))
    if f.date_to:
        daily = daily.where(Transaction.date <= f.date_to)

    balance = float(db.scalar(opening) or 0)
    points: list[dict] = []
    for day, net in db.execute(daily.order_by(Transaction.date)):
        net = float(net)
        if f.date_from and day < f.date_from:
            balance += net
            continue
        if not points and f.date_from and day > f.date_from:
            # Carry the balance in, so the line starts at the edge of the period.
            points.append({"date": f.date_from, "balance": r2(balance)})
        balance += net
        points.append({"date": day, "balance": r2(balance)})
    return points


def _months_between(first: str, last: str) -> list[str]:
    year, month = int(first[:4]), int(first[5:7])
    out = []
    while f"{year:04d}-{month:02d}" <= last:
        out.append(f"{year:04d}-{month:02d}")
        year, month = (year + 1, 1) if month == 12 else (year, month + 1)
    return out


def monthly_flows(db: Session, f: Filters) -> list[dict]:
    rows = db.execute(
        apply_filters(txn_select(Transaction.month, Group.kind, _SUM_IN, _SUM_OUT), f).group_by(
            Transaction.month, Group.kind
        )
    ).all()
    if not rows:
        return []
    by_month: dict[str, dict[str, tuple[float, float]]] = defaultdict(dict)
    for month, kind, money_in, money_out in rows:
        by_month[month][kind] = (float(money_in), float(money_out))
    # Quiet months still get a row, so the time axis has no holes.
    return [
        {"month": month, **_flows(by_month.get(month, {}))}
        for month in _months_between(min(by_month), max(by_month))
    ]


def category_spend(db: Session, f: Filters) -> list[dict]:
    """Spending per category (expense kind only), largest first."""
    total = _SUM_OUT - _SUM_IN
    rows = db.execute(
        apply_filters(
            txn_select(
                Category.id, Category.name, Category.icon, Category.is_fallback, total, func.count()
            ),
            f,
        )
        .where(Group.kind == "expense")
        .group_by(Category.id, Category.name, Category.icon, Category.is_fallback)
        .order_by(total.desc())
    ).all()
    spent = [(*row[:4], float(row[4]), row[5]) for row in rows if row[4] > 0]
    grand_total = sum(row[4] for row in spent)
    return [
        {
            "category_id": category_id,
            "name": name,
            "icon": icon,
            "is_fallback": is_fallback,
            "total": r2(amount),
            "count": count,
            "share": amount / grand_total,
        }
        for category_id, name, icon, is_fallback, amount, count in spent
    ]


def data_range(db: Session) -> tuple[date | None, date | None, int]:
    return db.execute(
        select(func.min(Transaction.date), func.max(Transaction.date), func.count())
    ).one()
