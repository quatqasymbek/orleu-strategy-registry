from __future__ import annotations

import os
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import streamlit as st
from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    UniqueConstraint,
    create_engine,
    delete,
    func,
    insert,
    select,
    update,
)
from sqlalchemy.engine import Engine
from sqlalchemy.exc import IntegrityError

from reference_data import DEPARTMENTS

BASE_DIR = Path(__file__).resolve().parent
LOCAL_DB = BASE_DIR / "data" / "orleu_registry.db"
metadata = MetaData()

users = Table(
    "users",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("username", String(80), nullable=False, unique=True),
    Column("password_hash", Text, nullable=False),
    Column("role", String(40), nullable=False),
    Column("department_id", String(40)),
    Column("display_name", String(300), nullable=False),
    Column("active", Boolean, nullable=False, default=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
)

weekly_entries = Table(
    "weekly_entries",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("week_id", String(20), nullable=False, index=True),
    Column("department_id", String(40), nullable=False, index=True),
    Column("direction_id", String(10), nullable=False),
    Column("task_id", String(20), nullable=False),
    Column("activity", Text, nullable=False),
    Column("result", Text, nullable=False, default=""),
    Column("deadline", Date),
    Column("status", String(30), nullable=False, default="planned"),
    Column("is_major", Boolean, nullable=False, default=False),
    Column("meeting_date", Date),
    Column("comment", Text, nullable=False, default=""),
    Column("created_by", String(80), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
)

report_requests = Table(
    "report_requests",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("week_id", String(20), nullable=False, index=True),
    Column("department_id", String(40), nullable=False, index=True),
    Column("note", Text, nullable=False, default=""),
    Column("active", Boolean, nullable=False, default=True),
    Column("requested_at", DateTime(timezone=True), nullable=False),
    Column("requested_by", String(80), nullable=False),
    UniqueConstraint("week_id", "department_id", name="uq_request_week_department"),
)

audit_log = Table(
    "audit_log",
    metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("username", String(80), nullable=False),
    Column("action", String(80), nullable=False),
    Column("entity_type", String(80), nullable=False),
    Column("entity_id", String(80)),
    Column("details", Text, nullable=False, default=""),
    Column("created_at", DateTime(timezone=True), nullable=False),
)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _read_secret_url() -> str | None:
    try:
        if "database" in st.secrets and "url" in st.secrets["database"]:
            return str(st.secrets["database"]["url"])
        if "connections" in st.secrets and "strategy_db" in st.secrets["connections"]:
            return str(st.secrets["connections"]["strategy_db"]["url"])
    except Exception:
        return None
    return None


def database_url() -> str:
    url = os.getenv("DATABASE_URL") or _read_secret_url()
    if not url:
        LOCAL_DB.parent.mkdir(parents=True, exist_ok=True)
        return f"sqlite:///{LOCAL_DB.as_posix()}"
    if url.startswith("postgres://"):
        url = "postgresql+psycopg://" + url[len("postgres://"):]
    elif url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://"):]
    return url


@st.cache_resource(show_spinner=False)
def get_engine() -> Engine:
    url = database_url()
    kwargs: dict[str, Any] = {"pool_pre_ping": True, "future": True}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False, "timeout": 30}
    else:
        kwargs.update({"pool_size": 5, "max_overflow": 10, "pool_recycle": 300})
    return create_engine(url, **kwargs)


def init_database() -> None:
    metadata.create_all(get_engine())


def fetch_all(stmt) -> list[dict[str, Any]]:
    with get_engine().connect() as conn:
        return [dict(row) for row in conn.execute(stmt).mappings().all()]


def fetch_one(stmt) -> dict[str, Any] | None:
    with get_engine().connect() as conn:
        row = conn.execute(stmt).mappings().first()
        return dict(row) if row else None


def execute(stmt) -> int | None:
    with get_engine().begin() as conn:
        result = conn.execute(stmt)
        try:
            return int(result.inserted_primary_key[0])
        except Exception:
            return None


def audit(username: str, action: str, entity_type: str, entity_id: Any = None, details: str = "") -> None:
    execute(
        insert(audit_log).values(
            username=username,
            action=action,
            entity_type=entity_type,
            entity_id=None if entity_id is None else str(entity_id),
            details=details,
            created_at=utcnow(),
        )
    )


def add_entry(values: dict[str, Any], username: str) -> int:
    now = utcnow()
    values = dict(values)
    values.update(created_by=username, created_at=now, updated_at=now)
    entry_id = execute(insert(weekly_entries).values(**values))
    audit(username, "create", "weekly_entry", entry_id, values.get("activity", "")[:300])
    return int(entry_id or 0)


def update_entry(entry_id: int, values: dict[str, Any], username: str) -> None:
    values = dict(values)
    values["updated_at"] = utcnow()
    execute(update(weekly_entries).where(weekly_entries.c.id == entry_id).values(**values))
    audit(username, "update", "weekly_entry", entry_id, values.get("activity", "")[:300])


def remove_entry(entry_id: int, username: str) -> None:
    execute(delete(weekly_entries).where(weekly_entries.c.id == entry_id))
    audit(username, "delete", "weekly_entry", entry_id, "")


def get_entry(entry_id: int) -> dict[str, Any] | None:
    return fetch_one(select(weekly_entries).where(weekly_entries.c.id == entry_id))


def get_entries(week_id: str, department_id: str | None = None) -> list[dict[str, Any]]:
    stmt = select(weekly_entries).where(weekly_entries.c.week_id == week_id)
    if department_id:
        stmt = stmt.where(weekly_entries.c.department_id == department_id)
    stmt = stmt.order_by(weekly_entries.c.department_id, weekly_entries.c.updated_at.desc())
    return fetch_all(stmt)


def get_active_request(week_id: str, department_id: str) -> dict[str, Any] | None:
    return fetch_one(
        select(report_requests).where(
            report_requests.c.week_id == week_id,
            report_requests.c.department_id == department_id,
            report_requests.c.active.is_(True),
        )
    )


def get_requested_department_ids(week_id: str) -> list[str]:
    rows = fetch_all(
        select(report_requests.c.department_id).where(
            report_requests.c.week_id == week_id,
            report_requests.c.active.is_(True),
        )
    )
    return [str(row["department_id"]) for row in rows]


def set_requests(week_id: str, department_ids: Iterable[str], note: str, username: str) -> None:
    now = utcnow()
    ids = list(dict.fromkeys(department_ids))
    with get_engine().begin() as conn:
        for department_id in ids:
            existing = conn.execute(
                select(report_requests.c.id).where(
                    report_requests.c.week_id == week_id,
                    report_requests.c.department_id == department_id,
                )
            ).first()
            if existing:
                conn.execute(
                    update(report_requests)
                    .where(report_requests.c.id == existing[0])
                    .values(note=note, active=True, requested_at=now, requested_by=username)
                )
            else:
                conn.execute(
                    insert(report_requests).values(
                        week_id=week_id,
                        department_id=department_id,
                        note=note,
                        active=True,
                        requested_at=now,
                        requested_by=username,
                    )
                )
    audit(username, "request_reports", "week", week_id, ",".join(ids))


def clear_requests(week_id: str, department_ids: Iterable[str], username: str) -> None:
    ids = list(dict.fromkeys(department_ids))
    stmt = update(report_requests).where(report_requests.c.week_id == week_id)
    if ids:
        stmt = stmt.where(report_requests.c.department_id.in_(ids))
    execute(stmt.values(active=False))
    audit(username, "clear_report_requests", "week", week_id, ",".join(ids) if ids else "all")


def reset_all_data(username: str) -> None:
    with get_engine().begin() as conn:
        conn.execute(delete(report_requests))
        conn.execute(delete(weekly_entries))
        conn.execute(delete(audit_log))
    audit(username, "reset", "database", None, "Operational data cleared")


def storage_label() -> str:
    return "PostgreSQL" if database_url().startswith("postgresql") else "SQLite (локально)"
