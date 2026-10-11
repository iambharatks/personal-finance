from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    Numeric,
    String,
    Text,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# Exact in Postgres, plain floats in Python. Totals are rounded to 2dp at the API edge.
Money = Numeric(14, 2, asdecimal=False)

# What a group means for the numbers. services/metrics.py is the only reader.
KINDS = ("income", "expense", "tax", "invest", "transfer", "neutral")

# Where a transaction's category came from. Re-categorising by rules only touches "rule".
CATEGORY_SOURCES = ("seed", "rule", "manual")


class Base(DeclarativeBase):
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )


class Account(Base):
    __tablename__ = "accounts"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    type: Mapped[str] = mapped_column(String(20))
    bank: Mapped[str] = mapped_column(String(50))
    account_mask: Mapped[str | None] = mapped_column(String(20))
    currency: Mapped[str] = mapped_column(String(3), default="INR")
    # Balance before the first imported transaction; running balance is derived from it.
    opening_balance: Mapped[float] = mapped_column(Money, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Group(Base):
    __tablename__ = "groups"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50), unique=True)
    kind: Mapped[str] = mapped_column(String(10))
    sort: Mapped[int] = mapped_column(Integer, default=0)


class Category(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    group_id: Mapped[int] = mapped_column(ForeignKey("groups.id"))
    icon: Mapped[str | None] = mapped_column(String(10))
    # Needs vs wants. NULL = not classified (card bills, charges, unlabelled).
    is_essential: Mapped[bool | None] = mapped_column(Boolean)
    # Catch-all bucket for payments no rule recognised ("unlabelled").
    is_fallback: Mapped[bool] = mapped_column(Boolean, default=False)
    monthly_budget: Mapped[float | None] = mapped_column(Money)

    group: Mapped[Group] = relationship()


class ImportBatch(Base):
    __tablename__ = "import_batches"

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"))
    filename: Mapped[str] = mapped_column(String(255))
    format: Mapped[str] = mapped_column(String(30))
    file_sha256: Mapped[str] = mapped_column(String(64))
    row_count: Mapped[int] = mapped_column(Integer)
    imported_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (Index("ix_transactions_account_date_seq", "account_id", "date", "seq"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    account_id: Mapped[int] = mapped_column(ForeignKey("accounts.id"))
    date: Mapped[date] = mapped_column(Date)
    # Position within the statement, so same-day rows keep the bank's order.
    seq: Mapped[int] = mapped_column(Integer, default=0)
    # YYYY-MM, stored so monthly grouping needs no database-specific date function.
    month: Mapped[str] = mapped_column(String(7), index=True)
    category_id: Mapped[int] = mapped_column(ForeignKey("categories.id"), index=True)
    category_source: Mapped[str] = mapped_column(String(10), default="manual")
    payee: Mapped[str] = mapped_column(String(200), default="")
    note: Mapped[str] = mapped_column(String(500), default="")
    money_in: Mapped[float] = mapped_column(Money, default=0)
    money_out: Mapped[float] = mapped_column(Money, default=0)
    # Balance printed on the statement. A cross-check only; never used for totals.
    statement_balance: Mapped[float | None] = mapped_column(Money)
    raw_remarks: Mapped[str | None] = mapped_column(Text)
    import_batch_id: Mapped[int | None] = mapped_column(ForeignKey("import_batches.id"))
    dedupe_key: Mapped[str | None] = mapped_column(String(64), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )

    account: Mapped[Account] = relationship()
    category: Mapped[Category] = relationship()


class LoginAttempt(Base):
    __tablename__ = "login_attempts"

    id: Mapped[int] = mapped_column(primary_key=True)
    ip: Mapped[str] = mapped_column(String(64), index=True)
    at: Mapped[datetime] = mapped_column(DateTime, index=True)
    ok: Mapped[bool] = mapped_column(Boolean)
