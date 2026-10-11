"""Maintenance commands. They act on whatever DATABASE_URL points at (local SQLite by
default), so each one prints its target first.

    uv run python -m app.cli migrate
    uv run python -m app.cli seed [--csv PATH]
    uv run python -m app.cli set-password [--write-env]
    uv run python -m app.cli backup
    uv run python -m app.cli openapi --out PATH
"""

import argparse
import getpass
import json
import secrets
import sys
from datetime import date, datetime
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session

from app.config import PRIVATE_DIR, SERVER_DIR, get_settings

DEFAULT_SEED_CSV = PRIVATE_DIR / "seed" / "transactions.csv"
ENV_FILE = PRIVATE_DIR / ".env"


def _announce_target() -> None:
    url = make_url(get_settings().sqlalchemy_url)
    where = url.database if url.drivername.startswith("sqlite") else f"{url.host}/{url.database}"
    print(f"Database: {url.get_backend_name()} -> {where}")


def migrate(_: argparse.Namespace) -> None:
    from alembic import command
    from alembic.config import Config

    _announce_target()
    if get_settings().sqlalchemy_url.startswith("sqlite"):
        PRIVATE_DIR.mkdir(exist_ok=True)
    command.upgrade(Config(str(SERVER_DIR / "alembic.ini")), "head")
    print("Schema is up to date.")


def seed(args: argparse.Namespace) -> None:
    from app.db import get_engine
    from app.seed import seed_from_csv

    _announce_target()
    csv_path = Path(args.csv)
    if not csv_path.exists():
        sys.exit(f"Seed file not found: {csv_path}")
    with Session(get_engine()) as db:
        result = seed_from_csv(db, csv_path)
    if result["skipped"]:
        print(f"Nothing to do: {result['reason']}.")
    else:
        print(
            f"Loaded {result['rows']} transactions into '{result['account']}' "
            f"({result['categories']} categories, opening balance {result['opening_balance']})."
        )


def set_password(args: argparse.Namespace) -> None:
    from app.auth import hash_password

    password = getpass.getpass("New password: ")
    if len(password) < 10:
        sys.exit("Use at least 10 characters.")
    if getpass.getpass("Repeat password: ") != password:
        sys.exit("Passwords do not match.")

    values = {
        "APP_PASSWORD_HASH": hash_password(password),
        "SESSION_SECRET": secrets.token_urlsafe(48),
    }
    if args.write_env:
        kept = []
        if ENV_FILE.exists():
            kept = [
                line
                for line in ENV_FILE.read_text(encoding="utf-8").splitlines()
                if line.split("=", 1)[0].strip() not in values
            ]
        ENV_FILE.parent.mkdir(exist_ok=True)
        lines = kept + [f"{key}={value}" for key, value in values.items()]
        ENV_FILE.write_text("\n".join(lines) + "\n", encoding="utf-8")
        print(f"Saved to {ENV_FILE}. Restart the server to apply.")
    else:
        print("\nSet these two environment variables on the host (they are secrets):\n")
        for key, value in values.items():
            print(f"{key}={value}")


def backup(_: argparse.Namespace) -> None:
    from app.db import get_engine
    from app.models import Base

    _announce_target()
    skip = {"login_attempts"}
    dump: dict[str, list[dict]] = {}
    with Session(get_engine()) as db:
        for table in Base.metadata.sorted_tables:
            if table.name not in skip:
                dump[table.name] = [dict(row._mapping) for row in db.execute(select(table))]

    out_dir = PRIVATE_DIR / "backups"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = out_dir / f"finance-{datetime.now():%Y%m%d-%H%M%S}.json"

    def encode(value):
        if isinstance(value, date | datetime):
            return value.isoformat()
        raise TypeError(type(value))

    out.write_text(json.dumps(dump, default=encode, ensure_ascii=False), encoding="utf-8")
    counts = ", ".join(f"{name}: {len(rows)}" for name, rows in dump.items())
    print(f"Wrote {out}\n{counts}")


def openapi(args: argparse.Namespace) -> None:
    from fastapi.openapi.utils import get_openapi

    from app.main import app

    schema = get_openapi(title=app.title, version=app.version, routes=app.routes)
    Path(args.out).write_text(json.dumps(schema, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {args.out}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="app.cli", description=__doc__.split("\n")[0])
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("migrate", help="create or upgrade the database schema").set_defaults(
        func=migrate
    )

    p_seed = sub.add_parser("seed", help="load the curated transactions CSV")
    p_seed.add_argument("--csv", default=str(DEFAULT_SEED_CSV))
    p_seed.set_defaults(func=seed)

    p_pw = sub.add_parser("set-password", help="create the login password hash")
    p_pw.add_argument("--write-env", action="store_true", help="save into private/.env")
    p_pw.set_defaults(func=set_password)

    sub.add_parser("backup", help="dump every table to private/backups/").set_defaults(func=backup)

    p_api = sub.add_parser("openapi", help="write the API schema for the client's types")
    p_api.add_argument("--out", required=True)
    p_api.set_defaults(func=openapi)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
