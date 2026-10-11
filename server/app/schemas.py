from datetime import date

from pydantic import BaseModel, Field


class LoginIn(BaseModel):
    password: str = Field(min_length=1, max_length=200)


class AuthStatus(BaseModel):
    authenticated: bool
    auth_required: bool


class Meta(BaseModel):
    min_date: date | None
    max_date: date | None
    txn_count: int


class AccountOut(BaseModel):
    id: int
    name: str
    type: str
    bank: str
    account_mask: str | None
    is_active: bool
    balance: float
    txn_count: int
    last_txn_date: date | None


class GroupOut(BaseModel):
    id: int
    name: str
    kind: str


class CategoryOut(BaseModel):
    id: int
    name: str
    icon: str | None
    is_essential: bool | None
    is_fallback: bool
    group: GroupOut


class TxnOut(BaseModel):
    id: int
    date: date
    account_id: int
    account: str
    category_id: int
    category: str
    category_icon: str | None
    is_fallback: bool
    group: str
    kind: str
    category_source: str
    payee: str
    note: str
    money_in: float
    money_out: float
    balance: float


class TxnPage(BaseModel):
    items: list[TxnOut]
    total: int
    page: int
    page_size: int
    sum_in: float
    sum_out: float


class TxnPatch(BaseModel):
    category_id: int | None = None
    payee: str | None = Field(default=None, max_length=200)
    note: str | None = Field(default=None, max_length=500)


class Kpis(BaseModel):
    income: float
    spending: float
    tax: float
    investing: float
    net_savings: float
    savings_rate: float | None
    invest_rate: float | None
    months: int
    avg_monthly_spend: float
    runway_months: float | None
    closing_balance: float
    txn_count: int


class BalancePoint(BaseModel):
    date: date
    balance: float


class MonthFlow(BaseModel):
    month: str
    income: float
    spending: float
    tax: float
    investing: float
    net_savings: float


class CategorySpend(BaseModel):
    category_id: int
    name: str
    icon: str | None
    is_fallback: bool
    total: float
    count: int
    share: float
