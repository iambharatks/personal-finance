from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_db
from app.filters import Filters, get_filters
from app.schemas import BalancePoint, CategorySpend, Kpis, MonthFlow
from app.services import metrics

router = APIRouter(tags=["dashboard"])


@router.get("/dashboard")
def dashboard(f: Filters = Depends(get_filters), db: Session = Depends(get_db)) -> Kpis:
    return Kpis(**metrics.kpis(db, f))


@router.get("/charts/balance")
def balance(f: Filters = Depends(get_filters), db: Session = Depends(get_db)) -> list[BalancePoint]:
    return [BalancePoint(**point) for point in metrics.balance_series(db, f)]


@router.get("/charts/monthly-flows")
def monthly_flows(
    f: Filters = Depends(get_filters), db: Session = Depends(get_db)
) -> list[MonthFlow]:
    return [MonthFlow(**row) for row in metrics.monthly_flows(db, f)]


@router.get("/charts/category-spend")
def category_spend(
    f: Filters = Depends(get_filters), db: Session = Depends(get_db)
) -> list[CategorySpend]:
    return [CategorySpend(**row) for row in metrics.category_spend(db, f)]
