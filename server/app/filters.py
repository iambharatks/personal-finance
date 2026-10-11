"""The one filter object. Every list, KPI and chart endpoint takes it as a dependency,
and the client keeps the same fields in the URL."""

from dataclasses import dataclass, field
from datetime import date
from typing import Annotated, Literal

from fastapi import Query
from sqlalchemy import Select, func, or_, select

from app.models import Category, Group, Transaction


@dataclass
class Filters:
    date_from: date | None = None
    date_to: date | None = None
    accounts: list[int] = field(default_factory=list)
    categories: list[int] = field(default_factory=list)
    groups: list[int] = field(default_factory=list)
    q: str | None = None
    min_amount: float | None = None
    max_amount: float | None = None
    direction: Literal["in", "out"] | None = None
    unlabelled: bool = False


def get_filters(
    date_from: Annotated[date | None, Query(alias="from")] = None,
    date_to: Annotated[date | None, Query(alias="to")] = None,
    account: Annotated[list[int] | None, Query()] = None,
    category: Annotated[list[int] | None, Query()] = None,
    group: Annotated[list[int] | None, Query()] = None,
    q: Annotated[str | None, Query(max_length=100)] = None,
    min_amount: Annotated[float | None, Query(alias="min", ge=0)] = None,
    max_amount: Annotated[float | None, Query(alias="max", ge=0)] = None,
    direction: Annotated[Literal["in", "out"] | None, Query(alias="dir")] = None,
    unlabelled: bool = False,
) -> Filters:
    return Filters(
        date_from=date_from,
        date_to=date_to,
        accounts=account or [],
        categories=category or [],
        groups=group or [],
        q=q.strip() if q and q.strip() else None,
        min_amount=min_amount,
        max_amount=max_amount,
        direction=direction,
        unlabelled=unlabelled,
    )


# One side is always zero, so the sum is the transaction's size.
AMOUNT = Transaction.money_in + Transaction.money_out


def txn_select(*columns) -> Select:
    """A select over transactions already joined to category and group."""
    return (
        select(*columns)
        .select_from(Transaction)
        .join(Category, Category.id == Transaction.category_id)
        .join(Group, Group.id == Category.group_id)
    )


def apply_filters(stmt: Select, f: Filters) -> Select:
    """Narrow a txn_select() statement to the filter."""
    if f.date_from:
        stmt = stmt.where(Transaction.date >= f.date_from)
    if f.date_to:
        stmt = stmt.where(Transaction.date <= f.date_to)
    if f.accounts:
        stmt = stmt.where(Transaction.account_id.in_(f.accounts))
    if f.categories:
        stmt = stmt.where(Transaction.category_id.in_(f.categories))
    if f.groups:
        stmt = stmt.where(Category.group_id.in_(f.groups))
    if f.q:
        needle = f.q.lower()
        stmt = stmt.where(
            or_(
                func.lower(Transaction.payee).contains(needle, autoescape=True),
                func.lower(Transaction.note).contains(needle, autoescape=True),
                func.lower(func.coalesce(Transaction.raw_remarks, "")).contains(
                    needle, autoescape=True
                ),
            )
        )
    if f.min_amount is not None:
        stmt = stmt.where(AMOUNT >= f.min_amount)
    if f.max_amount is not None:
        stmt = stmt.where(AMOUNT <= f.max_amount)
    if f.direction == "in":
        stmt = stmt.where(Transaction.money_in > 0)
    elif f.direction == "out":
        stmt = stmt.where(Transaction.money_out > 0)
    if f.unlabelled:
        stmt = stmt.where(Category.is_fallback.is_(True))
    return stmt
