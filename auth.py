from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
from datetime import datetime, timezone

import streamlit as st
from sqlalchemy import insert, select, update

from database import audit, execute, fetch_one, get_engine, users, utcnow
from export_patch import install_export_patch
from reference_data import DEPARTMENTS

install_export_patch()

ROLE_DEPARTMENT = "department"
ROLE_CHAIRMAN = "chairman"
ROLE_STRATEGY_ADMIN = "strategy_admin"

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


def _create_user_if_missing(username: str, password: str, role: str, department_id: str | None, display_name: str) -> None:
    with get_engine().begin() as conn:
        existing = conn.execute(select(users.c.id).where(users.c.username == username)).first()
        if existing:
            return
        conn.execute(
            insert(users).values(
                username=username,
                password_hash=hash_password(password),
                role=role,
                department_id=department_id,
                display_name=display_name,
                active=True,
                created_at=utcnow(),
            )
        )


def seed_default_users() -> None:
    _create_user_if_missing(
        "STRATEGY_ADMIN",
        DEFAULT_PRIVILEGED_PASSWORD,
        ROLE_STRATEGY_ADMIN,
        None,
        "Администратор реестра Стратегии",
    )
    _create_user_if_missing(
        "CHAIRMAN",
        DEFAULT_PRIVILEGED_PASSWORD,
        ROLE_CHAIRMAN,
        None,
        "Председатель Правления",
    )
    for dept in DEPARTMENTS:
        _create_user_if_missing(
            dept["id"],
            DEFAULT_DEPARTMENT_PASSWORD,
            ROLE_DEPARTMENT,
            dept["id"],
            dept["name"],
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
    audit(username, "reset_passwords", "users", None, "Defaults restored")


def authenticate(username: str, password: str) -> dict | None:
    user = fetch_one(select(users).where(users.c.username == username.strip().upper(), users.c.active.is_(True)))
    if not user or not verify_password(password, str(user["password_hash"])):
        return None
    audit(str(user["username"]), "login", "session", None, "")
    return user


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
    st.caption("Департаменты и филиалы: пароль 1234 · STRATEGY_ADMIN и CHAIRMAN: пароль 0000")


def current_user() -> dict | None:
    return st.session_state.get("user")


def logout() -> None:
    user = current_user()
    if user:
        audit(str(user["username"]), "logout", "session", None, "")
    st.session_state.clear()
    st.query_params.clear()
    st.rerun()
