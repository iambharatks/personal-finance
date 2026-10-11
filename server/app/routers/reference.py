"""Small lookup lists the UI needs everywhere: accounts, categories, data range."""

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session, joinedload

from app.db import get_db
from app.models import Account, Category, Group, Transaction
from app.schemas import AccountOut, CategoryOut, Meta
from app.services import metrics

router = APIRouter(tags=["reference"])


@router.get("/meta")
def meta(db: Session = Depends(get_db)) -> Meta:
    min_date, max_date, count = metrics.data_range(db)
    return Meta(min_date=min_date, max_date=max_date, txn_count=count)


@router.get("/accounts")
def list_accounts(db: Session = Depends(get_db)) -> list[AccountOut]:
    net = func.coalesce(func.sum(Transaction.money_in - Transaction.money_out), 0)
    rows = db.execute(
        select(Account, net, func.count(Transaction.id), func.max(Transaction.date))
        .outerjoin(Transaction, Transaction.account_id == Account.id)
        .group_by(Account.id)
        .order_by(Account.name)
    ).all()
    return [
        AccountOut(
            id=account.id,
            name=account.name,
            type=account.type,
            bank=account.bank,
            account_mask=account.account_mask,
            is_active=account.is_active,
            balance=metrics.r2(float(account.opening_balance) + float(moved)),
            txn_count=count,
            last_txn_date=last_date,
        )
        for account, moved, count, last_date in rows
    ]


@router.get("/categories")
def list_categories(db: Session = Depends(get_db)) -> list[CategoryOut]:
    categories = db.scalars(
        select(Category)
        .join(Group)
        .options(joinedload(Category.group))
        .order_by(Group.sort, Category.name)
    ).all()
    return [CategoryOut.model_validate(c, from_attributes=True) for c in categories]
