from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from collections import defaultdict

import streamlit as st
from sqlalchemy import insert, select, update

from database import audit, execute, fetch_one, get_engine, users, utcnow
from export_patch import install_export_patch
from reference_data import BLOCK_ORDER, DEPARTMENTS

install_export_patch()

ROLE_DEPARTMENT = "department"
ROLE_CHAIRMAN = "chairman"
ROLE_STRATEGY_ADMIN = "strategy_admin"

ADMIN_USERNAME = "ADMIN"
LEGACY_ADMIN_USERNAME = "STRATEGY_ADMIN"
DEFAULT_DEPARTMENT_PASSWORD = "1234"
DEFAULT_PRIVILEGED_PASSWORD = "0000"
PBKDF2_ITERATIONS = 120_000


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return "pbkdf2_sha256${}${}${}".format(
        PBKDF2_ITERATIONS,
        base64.urlsafe_b64encode(salt).decode("ascii"),
        base64.urlsafe_b64encode(digest).decode("ascii"),
    )


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, iterations, salt_text, digest_text = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        salt = base64.urlsafe_b64decode(salt_text.encode("ascii"))
        expected = base64.urlsafe_b64decode(digest_text.encode("ascii"))
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, int(iterations))
        return hmac.compare_digest(actual, expected)
    except Exception:
        return False


def _desired_accounts() -> list[dict]:
    accounts = [
        {
            "username": ADMIN_USERNAME,
            "password": DEFAULT_PRIVILEGED_PASSWORD,
            "role": ROLE_STRATEGY_ADMIN,
            "department_id": None,
            "display_name": "Администратор реестра Стратегии",
        },
        {
            "username": "CHAIRMAN",
            "password": DEFAULT_PRIVILEGED_PASSWORD,
            "role": ROLE_CHAIRMAN,
            "department_id": None,
            "display_name": "Председатель Правления",
        },
    ]
    accounts.extend(
        {
            "username": dept["id"],
            "password": DEFAULT_DEPARTMENT_PASSWORD,
            "role": ROLE_DEPARTMENT,
            "department_id": dept["id"],
            "display_name": dept["name"],
        }
        for dept in DEPARTMENTS
    )
    return accounts


def seed_default_users() -> None:
    """Create missing accounts and migrate STRATEGY_ADMIN to ADMIN.

    All checks and inserts use one transaction, which avoids dozens of
    sequential network round-trips when PostgreSQL is hosted in Supabase.
    Existing passwords are never overwritten during normal startup.
    """
    desired = _desired_accounts()

    with get_engine().begin() as conn:
        existing_rows = conn.execute(select(users)).mappings().all()
        existing = {str(row["username"]): dict(row) for row in existing_rows}

        legacy_admin = existing.get(LEGACY_ADMIN_USERNAME)
        current_admin = existing.get(ADMIN_USERNAME)

        if legacy_admin and not current_admin:
            conn.execute(
                update(users)
                .where(users.c.id == legacy_admin["id"])
                .values(
                    username=ADMIN_USERNAME,
                    role=ROLE_STRATEGY_ADMIN,
                    department_id=None,
                    display_name="Администратор реестра Стратегии",
                    active=True,
                )
            )
            migrated = dict(legacy_admin)
            migrated.update(
                username=ADMIN_USERNAME,
                role=ROLE_STRATEGY_ADMIN,
                department_id=None,
                display_name="Администратор реестра Стратегии",
                active=True,
            )
            existing.pop(LEGACY_ADMIN_USERNAME, None)
            existing[ADMIN_USERNAME] = migrated
        elif legacy_admin and current_admin and legacy_admin.get("active"):
            # Keep only the new login active when both records exist.
            conn.execute(
                update(users)
                .where(users.c.id == legacy_admin["id"])
                .values(active=False)
            )

        for account in desired:
            if account["username"] in existing:
                continue
            conn.execute(
                insert(users).values(
                    username=account["username"],
                    password_hash=hash_password(account["password"]),
                    role=account["role"],
                    department_id=account["department_id"],
                    display_name=account["display_name"],
                    active=True,
                    created_at=utcnow(),
                )
            )


def reset_default_passwords(username: str) -> None:
    with get_engine().begin() as conn:
        conn.execute(
            update(users)
            .where(users.c.role == ROLE_DEPARTMENT)
            .values(password_hash=hash_password(DEFAULT_DEPARTMENT_PASSWORD), active=True)
        )
        conn.execute(
            update(users)
            .where(users.c.role.in_([ROLE_CHAIRMAN, ROLE_STRATEGY_ADMIN]))
            .values(password_hash=hash_password(DEFAULT_PRIVILEGED_PASSWORD), active=True)
        )
        conn.execute(
            update(users)
            .where(users.c.username == LEGACY_ADMIN_USERNAME)
            .values(active=False)
        )
    audit(username, "reset_passwords", "users", None, "Defaults restored")


def authenticate(username: str, password: str) -> dict | None:
    normalized_username = username.strip().upper()
    user = fetch_one(
        select(users).where(
            users.c.username == normalized_username,
            users.c.active.is_(True),
        )
    )
    if not user or not verify_password(password, str(user["password_hash"])):
        return None
    audit(str(user["username"]), "login", "session", None, "")
    return user


def _render_login_directory() -> None:
    grouped: dict[str, list[dict]] = defaultdict(list)
    for department in DEPARTMENTS:
        grouped[department["block"]].append(department)

    st.markdown("### Справочник логинов")
    st.caption("Логины вводятся латинскими буквами в верхнем регистре. Пароли выдаются администратором системы.")

    with st.container(border=True):
        privileged_left, privileged_right = st.columns(2)
        with privileged_left:
            st.markdown("**Руководство**")
            st.markdown("`CHAIRMAN` — Председатель Правления")
        with privileged_right:
            st.markdown("**Администрирование**")
            st.markdown("`ADMIN` — администратор реестра Стратегии")

    columns = st.columns(2)
    for block_index, block in enumerate(BLOCK_ORDER):
        with columns[block_index % 2]:
            with st.container(border=True):
                st.markdown(f"**{block}**")
                lines = [f"`{dept['id']}` — {dept['name']}" for dept in grouped[block]]
                st.markdown("  \n".join(lines))


def login_screen() -> None:
    st.markdown(
        """
        <div class="login-shell">
          <div class="login-card">
            <div class="login-eyebrow">СТРАТЕГИЯ РАЗВИТИЯ 2025–2029 · ПЛАН НА 2026 ГОД</div>
            <div class="login-title">Реестр еженедельного исполнения</div>
            <div class="login-sub">Корпоративная форма для подразделений и свод руководителя.</div>
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.form("login", clear_on_submit=False):
        username = st.text_input("Логин").strip().upper()
        password = st.text_input("Пароль", type="password")
        submitted = st.form_submit_button("Войти", type="primary", use_container_width=True)
    if submitted:
        user = authenticate(username, password)
        if user:
            st.session_state["user"] = user
            st.query_params.clear()
            st.rerun()
        else:
            st.error("Неверный логин или пароль.")

    st.caption("Тестовый режим: подразделения — пароль 1234; ADMIN и CHAIRMAN — пароль 0000")
    _render_login_directory()


def current_user() -> dict | None:
    return st.session_state.get("user")


def logout() -> None:
    user = current_user()
    if user:
        audit(str(user["username"]), "logout", "session", None, "")
    st.session_state.clear()
    st.query_params.clear()
    st.rerun()
