from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_db
from app.filters import AMOUNT, Filters, apply_filters, get_filters, txn_select
from app.models import Account, Category, Group, Transaction
from app.schemas import TxnOut, TxnPage, TxnPatch
from app.services.metrics import r2

router = APIRouter(prefix="/transactions", tags=["transactions"])

SortKey = Literal["date", "payee", "category", "account", "money_in", "money_out", "amount"]

_SORT_COLUMNS = {
    "date": Transaction.date,
    "payee": func.lower(Transaction.payee),
    "category": Category.name,
    "account": Account.name,
    "money_in": Transaction.money_in,
    "money_out": Transaction.money_out,
    "amount": AMOUNT,
}

# Running balance per account in statement order, computed over ALL of an account's rows
# so it stays right whatever the filter or sort.
_RUNNING = (
    select(
        Transaction.id.label("txn_id"),
        func.sum(Transaction.money_in - Transaction.money_out)
        .over(
            partition_by=Transaction.account_id,
            order_by=(Transaction.date, Transaction.seq, Transaction.id),
        )
        .label("moved"),
    )
).subquery()

_COLUMNS = (
    Transaction.id,
    Transaction.date,
    Transaction.account_id,
    Account.name.label("account"),
    Transaction.category_id,
    Category.name.label("category"),
    Category.icon.label("category_icon"),
    Category.is_fallback,
    Group.name.label("group"),
    Group.kind,
    Transaction.category_source,
    Transaction.payee,
    Transaction.note,
    Transaction.money_in,
    Transaction.money_out,
    (Account.opening_balance + _RUNNING.c.moved).label("balance"),
)


def _rows_select():
    return (
        txn_select(*_COLUMNS)
        .join(Account, Account.id == Transaction.account_id)
        .join(_RUNNING, _RUNNING.c.txn_id == Transaction.id)
    )


def _to_out(row) -> TxnOut:
    data = dict(row._mapping)
    for key in ("money_in", "money_out", "balance"):
        data[key] = r2(float(data[key]))
    return TxnOut(**data)


@router.get("")
def list_transactions(
    f: Filters = Depends(get_filters),
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=200)] = 50,
    sort: SortKey = "date",
    order: Literal["asc", "desc"] = "desc",
    db: Session = Depends(get_db),
) -> TxnPage:
    total, sum_in, sum_out = db.execute(
        apply_filters(
            txn_select(
                func.count(),
                func.coalesce(func.sum(Transaction.money_in), 0),
                func.coalesce(func.sum(Transaction.money_out), 0),
            ),
            f,
        )
    ).one()

    direction = (lambda c: c.asc()) if order == "asc" else (lambda c: c.desc())
    # Statement order breaks ties, so paging is stable.
    ordering = [direction(c) for c in (_SORT_COLUMNS[sort], Transaction.date, Transaction.seq)]
    rows = db.execute(
        apply_filters(_rows_select(), f)
        .order_by(*ordering, direction(Transaction.id))
        .limit(page_size)
        .offset((page - 1) * page_size)
    ).all()

    return TxnPage(
        items=[_to_out(row) for row in rows],
        total=total,
        page=page,
        page_size=page_size,
        sum_in=r2(float(sum_in)),
        sum_out=r2(float(sum_out)),
    )


@router.patch("/{txn_id}")
def update_transaction(txn_id: int, patch: TxnPatch, db: Session = Depends(get_db)) -> TxnOut:
    txn = db.get(Transaction, txn_id)
    if txn is None:
        raise HTTPException(status_code=404, detail="Transaction not found")

    if patch.category_id is not None and patch.category_id != txn.category_id:
        if db.get(Category, patch.category_id) is None:
            raise HTTPException(status_code=422, detail="Unknown category")
        txn.category_id = patch.category_id
        # A hand-picked category is never overwritten by the rule engine.
        txn.category_source = "manual"
    if patch.payee is not None:
        txn.payee = patch.payee.strip()
    if patch.note is not None:
        txn.note = patch.note.strip()
    db.commit()

    return _to_out(db.execute(_rows_select().where(Transaction.id == txn_id)).one())
