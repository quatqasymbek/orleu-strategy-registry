from __future__ import annotations

import csv
import io
from collections import defaultdict
from datetime import date

import streamlit as st
from sqlalchemy import select

from auth import (
    DEFAULT_DEPARTMENT_PASSWORD,
    DEFAULT_PRIVILEGED_PASSWORD,
    ROLE_CHAIRMAN,
    ROLE_DEPARTMENT,
    ROLE_STRATEGY_ADMIN,
    current_user,
    login_screen,
    logout,
    reset_default_passwords,
    seed_default_users,
)
from database import (
    add_entry,
    clear_requests,
    get_active_request,
    get_entries,
    get_entry,
    get_requested_department_ids,
    init_database,
    remove_entry,
    reset_all_data,
    set_requests,
    storage_label,
    update_entry,
)
from reference_data import (
    BLOCK_ORDER,
    DEPARTMENT_BY_ID,
    DEPARTMENTS,
    DIRECTIONS,
    DIRECTION_BY_ID,
    STATUS_LABELS,
    STATUS_ORDER,
    TASKS,
    TASK_BY_ID,
)
from ui import (
    current_week_id,
    department_name,
    fmt_date,
    fmt_updated,
    inject_css,
    parse_week_id,
    render_header,
    safe,
    status_stamp,
)

st.set_page_config(
    page_title="Реестр еженедельного исполнения — Өрлеу",
    page_icon="📋",
    layout="wide",
    initial_sidebar_state="collapsed",
)
inject_css()
init_database()
seed_default_users()

# Query-parameter actions.
params = st.query_params
if params.get("logout") == "1":
    logout()

user = current_user()
if not user:
    login_screen()
    st.stop()

week_id = str(params.get("week") or current_week_id())
try:
    parse_week_id(week_id)
except Exception:
    week_id = current_week_id()

if user["role"] == ROLE_DEPARTMENT:
    mode = "dept"
elif user["role"] == ROLE_CHAIRMAN:
    mode = "lead"
else:
    mode = str(params.get("mode") or "lead")
    if mode not in {"dept", "lead"}:
        mode = "lead"

render_header(user, week_id, mode)


def can_edit_department(department_id: str) -> bool:
    if user["role"] == ROLE_STRATEGY_ADMIN:
        return True
    return user["role"] == ROLE_DEPARTMENT and user.get("department_id") == department_id


def default_department() -> str:
    if user["role"] == ROLE_DEPARTMENT:
        return str(user["department_id"])
    return str(st.session_state.get("admin_department") or DEPARTMENTS[0]["id"])


@st.dialog("Редактировать запись", width="large")
def edit_entry_dialog(entry_id: int) -> None:
    entry = get_entry(entry_id)
    if not entry:
        st.error("Запись не найдена.")
        return
    if not can_edit_department(str(entry["department_id"])):
        st.error("Нет прав для изменения этой записи.")
        return

    direction_ids = [row["id"] for row in DIRECTIONS]
    current_direction = str(entry["direction_id"])
    direction_id = st.selectbox(
        "Стратегическое направление",
        direction_ids,
        index=direction_ids.index(current_direction),
        format_func=lambda value: DIRECTION_BY_ID[value]["name"],
        key=f"edit_direction_{entry_id}",
    )
    task_options = [row["id"] for row in TASKS if row["direction_id"] == direction_id]
    current_task = str(entry["task_id"])
    task_id = st.selectbox(
        "Задача",
        task_options,
        index=task_options.index(current_task) if current_task in task_options else 0,
        format_func=lambda value: TASK_BY_ID[value]["name"],
        key=f"edit_task_{entry_id}_{direction_id}",
    )
    activity = st.text_area("Мероприятие / что делаем на этой неделе", value=str(entry["activity"]), key=f"edit_activity_{entry_id}")
    c1, c2 = st.columns(2)
    with c1:
        result = st.text_input("Ожидаемый / фактический результат", value=str(entry["result"] or ""), key=f"edit_result_{entry_id}")
    with c2:
        deadline = st.date_input("Срок (дедлайн)", value=entry["deadline"], key=f"edit_deadline_{entry_id}")
    c3, c4 = st.columns(2)
    with c3:
        status = st.selectbox(
            "Статус",
            STATUS_ORDER,
            index=STATUS_ORDER.index(str(entry["status"])),
            format_func=lambda value: STATUS_LABELS[value],
            key=f"edit_status_{entry_id}",
        )
    with c4:
        is_major = st.checkbox("Требует очного доклада Председателю", value=bool(entry["is_major"]), key=f"edit_major_{entry_id}")
    meeting_date = st.date_input(
        "Дата очного доклада (для крупного проекта)",
        value=entry["meeting_date"],
        key=f"edit_meeting_{entry_id}",
    )
    comment = st.text_input("Комментарий / риски", value=str(entry["comment"] or ""), key=f"edit_comment_{entry_id}")

    c5, c6 = st.columns(2)
    with c5:
        if st.button("Сохранить изменения", type="primary", use_container_width=True, key=f"save_edit_{entry_id}"):
            if not activity.strip():
                st.error("Заполните мероприятие.")
            else:
                update_entry(
                    entry_id,
                    {
                        "direction_id": direction_id,
                        "task_id": task_id,
                        "activity": activity.strip(),
                        "result": result.strip(),
                        "deadline": deadline,
                        "status": status,
                        "is_major": is_major,
                        "meeting_date": meeting_date if is_major else None,
                        "comment": comment.strip(),
                    },
                    str(user["username"]),
                )
                st.toast("Запись обновлена")
                st.rerun()
    with c6:
        if st.button("Удалить запись", type="secondary", use_container_width=True, key=f"delete_edit_{entry_id}"):
            remove_entry(entry_id, str(user["username"]))
            st.toast("Запись удалена")
            st.rerun()


def render_entry_card(entry: dict, index: int, editable: bool) -> None:
    direction_name = DIRECTION_BY_ID.get(str(entry["direction_id"]), {}).get("name", str(entry["direction_id"]))
    task_name = TASK_BY_ID.get(str(entry["task_id"]), {}).get("name", str(entry["task_id"]))
    major = '<span class="major-flag">Крупный</span>' if entry["is_major"] else ""
    st.markdown(
        f"""
        <div class="entry">
          <div style="display:flex;justify-content:space-between;gap:10px;align-items:flex-start">
            <div><span class="entry-num">№ {index}</span><div class="entry-task">{safe(direction_name)} · {safe(task_name)}</div></div>
            <div>{status_stamp(str(entry['status']))} {major}</div>
          </div>
          <div class="entry-activity">{safe(entry['activity'])}</div>
          <div class="entry-meta">
            <span><b>Результат:</b> {safe(entry['result'] or '—')}</span>
            <span><b>Срок:</b> {fmt_date(entry['deadline'])}</span>
            <span><b>Доклад:</b> {fmt_date(entry['meeting_date']) if entry['is_major'] else '—'}</span>
          </div>
          <div class="entry-meta" style="margin-top:6px"><span><b>Комментарий:</b> {safe(entry['comment'] or '—')}</span><span class="small-note">обновлено {fmt_updated(entry['updated_at'])}</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if editable:
        c1, c2, c3 = st.columns([1, 1, 5])
        with c1:
            if st.button("Изменить", key=f"edit_btn_{entry['id']}", use_container_width=True):
                edit_entry_dialog(int(entry["id"]))
        with c2:
            if st.button("Удалить", key=f"delete_btn_{entry['id']}", use_container_width=True):
                st.session_state["confirm_delete"] = int(entry["id"])
        if st.session_state.get("confirm_delete") == int(entry["id"]):
            st.warning("Удалить эту запись без возможности восстановления?")
            d1, d2 = st.columns(2)
            with d1:
                if st.button("Да, удалить", type="primary", key=f"confirm_delete_{entry['id']}"):
                    remove_entry(int(entry["id"]), str(user["username"]))
                    st.session_state.pop("confirm_delete", None)
                    st.rerun()
            with d2:
                if st.button("Отмена", key=f"cancel_delete_{entry['id']}"):
                    st.session_state.pop("confirm_delete", None)
                    st.rerun()


def department_view() -> None:
    if user["role"] == ROLE_STRATEGY_ADMIN:
        labels = {f"{row['id']} — {row['name']}": row["id"] for row in DEPARTMENTS}
        selected_label = st.selectbox("Департамент / лаборатория / филиал", list(labels), key="admin_department_selector")
        department_id = labels[selected_label]
        st.session_state["admin_department"] = department_id
        st.markdown('<div class="admin-note">Режим администратора: можно открыть кабинет любого подразделения и при необходимости внести техническое исправление.</div>', unsafe_allow_html=True)
    else:
        department_id = default_department()
        with st.container(border=True):
            st.markdown('<div class="panel-title">Подразделение</div>', unsafe_allow_html=True)
            st.write(department_name(department_id))

    request = get_active_request(week_id, department_id)
    if request:
        note = str(request["note"] or "Пожалуйста, заполните и сохраните статус по вашим мероприятиям.")
        st.markdown(
            f'<div class="banner"><div class="banner-dot">СРОЧ<br>НО</div><div><b>Запрошен отчёт на эту неделю</b><span>{safe(note)}</span></div></div>',
            unsafe_allow_html=True,
        )

    editable = can_edit_department(department_id)
    if editable:
        with st.container(border=True):
            st.markdown(f'<div class="panel-title">Новая запись <span class="entry-num">{safe(department_id)}</span></div>', unsafe_allow_html=True)
            direction_ids = [row["id"] for row in DIRECTIONS]
            c1, c2 = st.columns(2)
            with c1:
                direction_id = st.selectbox(
                    "Стратегическое направление",
                    direction_ids,
                    format_func=lambda value: DIRECTION_BY_ID[value]["name"],
                    key=f"new_direction_{department_id}_{week_id}",
                )
            task_options = [row["id"] for row in TASKS if row["direction_id"] == direction_id]
            with c2:
                task_id = st.selectbox(
                    "Задача",
                    task_options,
                    format_func=lambda value: TASK_BY_ID[value]["name"],
                    key=f"new_task_{department_id}_{week_id}_{direction_id}",
                )
            activity = st.text_area(
                "Мероприятие / что делаем на этой неделе",
                placeholder="Например: Разработка методических рекомендаций по профориентационной работе",
                key=f"new_activity_{department_id}_{week_id}",
            )
            c3, c4 = st.columns(2)
            with c3:
                result = st.text_input(
                    "Ожидаемый / фактический результат",
                    placeholder="Например: подготовлен проект методрекомендаций, 3 из 5 разделов",
                    key=f"new_result_{department_id}_{week_id}",
                )
            with c4:
                deadline = st.date_input("Срок (дедлайн)", value=None, key=f"new_deadline_{department_id}_{week_id}")
            c5, c6 = st.columns(2)
            with c5:
                status = st.selectbox(
                    "Статус",
                    STATUS_ORDER,
                    format_func=lambda value: STATUS_LABELS[value],
                    key=f"new_status_{department_id}_{week_id}",
                )
            with c6:
                is_major = st.checkbox("Требует очного доклада Председателю", key=f"new_major_{department_id}_{week_id}")
            c7, c8 = st.columns(2)
            with c7:
                meeting_date = st.date_input(
                    "Дата очного доклада (если требуется)",
                    value=None,
                    key=f"new_meeting_{department_id}_{week_id}",
                    disabled=not is_major,
                )
            with c8:
                comment = st.text_input(
                    "Комментарий / риски",
                    placeholder="Кратко: препятствия, потребности, решения",
                    key=f"new_comment_{department_id}_{week_id}",
                )
            if st.button("Добавить запись", type="primary", key=f"add_entry_{department_id}_{week_id}"):
                if not activity.strip():
                    st.error("Заполните поле «Мероприятие». ")
                elif is_major and meeting_date is None:
                    st.error("Для крупного проекта укажите дату очного доклада.")
                else:
                    add_entry(
                        {
                            "week_id": week_id,
                            "department_id": department_id,
                            "direction_id": direction_id,
                            "task_id": task_id,
                            "activity": activity.strip(),
                            "result": result.strip(),
                            "deadline": deadline,
                            "status": status,
                            "is_major": is_major,
                            "meeting_date": meeting_date if is_major else None,
                            "comment": comment.strip(),
                        },
                        str(user["username"]),
                    )
                    for key in list(st.session_state):
                        if key.startswith("new_") and f"_{department_id}_{week_id}" in key:
                            del st.session_state[key]
                    st.toast("Запись добавлена")
                    st.rerun()

    entries = get_entries(week_id, department_id)
    with st.container(border=True):
        st.markdown(f'<div class="panel-title">Записи на неделю <span class="entry-num">{len(entries)}</span></div>', unsafe_allow_html=True)
        if not entries:
            st.markdown('<div class="empty-note">На выбранную неделю записи ещё не добавлены.</div>', unsafe_allow_html=True)
        for index, entry in enumerate(entries, start=1):
            render_entry_card(entry, index, editable)


def export_week_csv(entries: list[dict]) -> bytes:
    output = io.StringIO()
    fieldnames = [
        "week_id", "department_id", "direction", "task", "activity", "result",
        "deadline", "status", "is_major", "meeting_date", "comment", "updated_at",
    ]
    writer = csv.DictWriter(output, fieldnames=fieldnames)
    writer.writeheader()
    for row in entries:
        writer.writerow(
            {
                "week_id": row["week_id"],
                "department_id": row["department_id"],
                "direction": DIRECTION_BY_ID.get(str(row["direction_id"]), {}).get("name", row["direction_id"]),
                "task": TASK_BY_ID.get(str(row["task_id"]), {}).get("name", row["task_id"]),
                "activity": row["activity"],
                "result": row["result"],
                "deadline": row["deadline"],
                "status": STATUS_LABELS.get(str(row["status"]), row["status"]),
                "is_major": "Да" if row["is_major"] else "Нет",
                "meeting_date": row["meeting_date"],
                "comment": row["comment"],
                "updated_at": row["updated_at"],
            }
        )
    return output.getvalue().encode("utf-8-sig")


def request_panel() -> None:
    with st.container(border=True):
        st.markdown('<div class="panel-title">Запросить отчёт у департаментов</div>', unsafe_allow_html=True)
        st.caption("Отмеченные подразделения увидят баннер-напоминание в своём кабинете.")
        options = [row["id"] for row in DEPARTMENTS]
        current_requested = get_requested_department_ids(week_id)
        selected = st.multiselect(
            "Департаменты / филиалы",
            options,
            default=current_requested,
            format_func=lambda value: DEPARTMENT_BY_ID[value]["name"],
            key=f"request_departments_{week_id}",
        )
        note = st.text_input(
            "Пояснение для департаментов (необязательно)",
            placeholder="Например: до пятницы 17:00, готовимся к докладу Председателю",
            key=f"request_note_{week_id}",
        )
        c1, c2, c3 = st.columns([1, 1, 3])
        with c1:
            if st.button("Отправить запрос", type="primary", key=f"send_request_{week_id}", use_container_width=True):
                if not selected:
                    st.warning("Выберите хотя бы одно подразделение.")
                else:
                    set_requests(week_id, selected, note.strip(), str(user["username"]))
                    st.toast("Запрос отправлен")
                    st.rerun()
        with c2:
            if st.button("Снять запрос", key=f"clear_request_{week_id}", use_container_width=True):
                clear_requests(week_id, selected, str(user["username"]))
                st.toast("Запрос снят")
                st.rerun()


@st.fragment(run_every="25s")
def leadership_live() -> None:
    entries = get_entries(week_id)
    total = len(entries)
    done = sum(row["status"] == "done" for row in entries)
    progress = sum(row["status"] == "in_progress" for row in entries)
    risk = sum(row["status"] in {"risk", "overdue"} for row in entries)
    major = sum(bool(row["is_major"]) for row in entries)
    st.markdown(
        f"""
        <div class="stat-strip">
          <div class="stat-card"><div class="n">{total}</div><div class="l">Всего записей</div></div>
          <div class="stat-card acc-done"><div class="n">{done}</div><div class="l">Выполнено</div></div>
          <div class="stat-card acc-progress"><div class="n">{progress}</div><div class="l">В работе</div></div>
          <div class="stat-card acc-risk"><div class="n">{risk}</div><div class="l">Риск / просрочка</div></div>
          <div class="stat-card acc-major"><div class="n">{major}</div><div class="l">Крупных проектов</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.container(border=True):
        h1, h2 = st.columns([3, 1])
        with h1:
            st.markdown('<div class="panel-title">Свод по подразделениям</div>', unsafe_allow_html=True)
        with h2:
            st.markdown('<div class="small-note" style="text-align:right">автообновление каждые 25 секунд</div>', unsafe_allow_html=True)
        f1, f2 = st.columns([1, 1])
        with f1:
            filter_status = st.selectbox(
                "Статус",
                [""] + STATUS_ORDER,
                format_func=lambda value: "Все статусы" if not value else STATUS_LABELS[value],
                key=f"filter_status_{week_id}",
            )
        with f2:
            major_only = st.checkbox("Только крупные проекты", key=f"filter_major_{week_id}")

        by_department: dict[str, list[dict]] = defaultdict(list)
        for row in entries:
            by_department[str(row["department_id"])].append(row)

        html_parts: list[str] = []
        for block in BLOCK_ORDER:
            html_parts.append(f'<div class="block-title">{safe(block)}</div>')
            for dept in [row for row in DEPARTMENTS if row["block"] == block]:
                raw_rows = by_department.get(dept["id"], [])
                filtered_rows = [
                    row for row in raw_rows
                    if (not filter_status or row["status"] == filter_status)
                    and (not major_only or row["is_major"])
                ]
                last_updated = max((row["updated_at"] for row in raw_rows), default=None)
                right = f'<span class="dept-updated">обновлено {fmt_updated(last_updated)}</span>' if raw_rows else '<span class="dept-updated stale">нет отчёта</span>'
                html_parts.append(f'<div class="dept-row"><div class="dept-head"><div class="dept-name">{safe(dept["name"])}</div>{right}</div>')
                if not raw_rows:
                    html_parts.append('<div class="no-report">Отчёт по неделе ещё не подан.</div>')
                elif not filtered_rows:
                    html_parts.append('<div class="no-report">Нет записей, соответствующих выбранному фильтру.</div>')
                else:
                    for row in filtered_rows:
                        major_flag = '<span class="major-flag">Крупный</span>' if row["is_major"] else ""
                        html_parts.append(
                            f'<div class="mini-entry">{status_stamp(str(row["status"]))}'
                            f'<span class="txt">{safe(row["activity"])} {major_flag}</span>'
                            f'<span class="dl">{fmt_date(row["deadline"])}</span></div>'
                        )
                html_parts.append('</div>')
        st.markdown("".join(html_parts), unsafe_allow_html=True)

    with st.container(border=True):
        st.markdown('<div class="panel-title">График очных докладов Председателю</div>', unsafe_allow_html=True)
        meetings = sorted(
            [row for row in entries if row["is_major"] and row["meeting_date"]],
            key=lambda row: row["meeting_date"],
        )
        if not meetings:
            st.markdown('<div class="empty-note">Крупные проекты с датой очного доклада не отмечены.</div>', unsafe_allow_html=True)
        else:
            parts = []
            for row in meetings:
                parts.append(
                    f'<div class="timeline-item"><div class="timeline-date">{fmt_date(row["meeting_date"])}</div>'
                    f'<div class="timeline-body"><b>{safe(row["activity"])}</b>'
                    f'<span>{safe(department_name(str(row["department_id"])))} · {safe(TASK_BY_ID.get(str(row["task_id"]), {}).get("name", row["task_id"]))} · статус: {safe(STATUS_LABELS.get(str(row["status"]), row["status"]))}</span></div></div>'
                )
            st.markdown("".join(parts), unsafe_allow_html=True)


def administration_panel() -> None:
    if user["role"] != ROLE_STRATEGY_ADMIN:
        return
    with st.expander("Администрирование и экспорт"):
        st.write(f"Хранилище данных: **{storage_label()}**")
        st.caption("Для Streamlit Community Cloud используйте внешнюю PostgreSQL-базу через Secrets.")
        entries = get_entries(week_id)
        st.download_button(
            "Скачать текущую неделю в CSV",
            data=export_week_csv(entries),
            file_name=f"orleu-{week_id}.csv",
            mime="text/csv",
        )
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Сбросить пароли по умолчанию"):
                reset_default_passwords(str(user["username"]))
                st.success(f"Подразделения: {DEFAULT_DEPARTMENT_PASSWORD}; администратор и Председатель: {DEFAULT_PRIVILEGED_PASSWORD}")
        with c2:
            confirm = st.checkbox("Разрешить очистку всех рабочих данных", key="allow_reset_data")
            if st.button("Очистить записи и запросы", disabled=not confirm):
                reset_all_data(str(user["username"]))
                st.success("Рабочие данные очищены.")
                st.rerun()


def leadership_view() -> None:
    request_panel()
    leadership_live()
    administration_panel()


if mode == "dept":
    department_view()
else:
    leadership_view()
