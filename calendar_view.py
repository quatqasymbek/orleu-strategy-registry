from __future__ import annotations

import calendar
import html
from collections import defaultdict
from datetime import date, datetime, timedelta
from typing import Any

import streamlit as st
from sqlalchemy import and_, or_, select

from database import fetch_all, weekly_entries
from reference_data import STATUS_LABELS, STATUS_ORDER

CALENDAR_CSS = r"""
<style>
/* Restore Streamlit's password visibility icon after the global Roboto rule. */
[data-testid="stTextInput"] button [data-testid="stIconMaterial"],
[data-testid="stTextInput"] button span[data-testid="stIconMaterial"]{
  font-family:"Material Symbols Rounded","Material Symbols Outlined","Material Icons"!important;
  font-weight:normal!important;
  font-style:normal!important;
  font-size:20px!important;
  line-height:1!important;
  letter-spacing:normal!important;
  text-transform:none!important;
  white-space:nowrap!important;
  word-wrap:normal!important;
  direction:ltr!important;
  font-feature-settings:"liga"!important;
  -webkit-font-feature-settings:"liga"!important;
  font-variation-settings:"FILL" 0,"wght" 400,"GRAD" 0,"opsz" 20!important;
}
[data-testid="stTextInput"] button{
  min-width:38px!important;
  width:38px!important;
  overflow:hidden!important;
}

.calendar-card{margin-top:4px;}
.calendar-heading{display:flex;align-items:center;justify-content:space-between;gap:10px;margin:0 0 10px;}
.calendar-heading b{font-size:13.5px;color:var(--navy)!important;}
.calendar-heading span{font-size:10.5px;color:var(--muted)!important;}
.month-calendar{border:1px solid var(--border);border-radius:9px;background:#fff;overflow:hidden;margin-bottom:14px;}
.month-title{padding:10px 12px;background:#F3F6F9;border-bottom:1px solid var(--border);font-size:13px;font-weight:700;color:var(--navy)!important;text-align:center;text-transform:capitalize;}
.calendar-grid{display:grid;grid-template-columns:repeat(7,minmax(0,1fr));}
.calendar-weekday{padding:6px 1px;text-align:center;background:#FAFBFC;border-bottom:1px solid var(--border);font-size:9px;font-weight:700;color:var(--muted)!important;text-transform:uppercase;}
.calendar-day{position:relative;min-height:49px;padding:5px 4px;border-right:1px solid #EDF1F5;border-bottom:1px solid #EDF1F5;background:#fff;overflow:hidden;}
.calendar-day:nth-child(7n){border-right:0;}
.calendar-day.other{background:#FAFBFC;color:#B0BAC5!important;}
.calendar-day.weekend{background:#FCFAF7;}
.calendar-day.in-week{box-shadow:inset 0 0 0 1px rgba(37,88,138,.18);background:#F7FAFD;}
.calendar-day.today{box-shadow:inset 0 0 0 2px var(--blue);}
.calendar-day .day-number{font-size:10.5px;font-weight:600;color:var(--text-soft)!important;line-height:1;}
.calendar-day.today .day-number{color:var(--blue)!important;font-weight:700;}
.calendar-dots{display:flex;align-items:center;gap:3px;flex-wrap:wrap;margin-top:7px;}
.calendar-dot{width:7px;height:7px;border-radius:50%;display:inline-block;box-shadow:0 0 0 1px rgba(0,0,0,.05);}
.calendar-dot.planned{background:#7F8B97;}
.calendar-dot.in_progress{background:#25588A;}
.calendar-dot.done{background:#2F7F6E;}
.calendar-dot.risk{background:#A96B00;}
.calendar-dot.overdue{background:#B14A3A;}
.calendar-dot.meeting{width:8px;height:8px;border-radius:2px;background:#002147;transform:rotate(45deg);}
.calendar-more{font-size:8.5px;color:var(--muted)!important;line-height:1;}
.calendar-legend{display:flex;gap:8px 12px;flex-wrap:wrap;padding:2px 0 12px;font-size:10px;color:var(--muted)!important;}
.calendar-legend span{display:inline-flex;align-items:center;gap:4px;color:var(--muted)!important;}
.calendar-list{border-top:1px solid var(--border);padding-top:10px;margin-top:2px;}
.calendar-list-title{font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:.35px;color:var(--blue)!important;margin-bottom:7px;}
.calendar-list-item{display:flex;gap:8px;padding:8px 0;border-top:1px dotted var(--border);}
.calendar-list-item:first-of-type{border-top:0;}
.calendar-list-date{min-width:42px;font-size:10.5px;font-weight:700;color:var(--navy)!important;}
.calendar-list-body{min-width:0;flex:1;}
.calendar-list-body b{display:block;font-size:11.5px;line-height:1.3;color:var(--text)!important;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}
.calendar-list-body span{font-size:9.5px;color:var(--muted)!important;}
.calendar-summary{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:8px 0 12px;}
.calendar-summary div{border:1px solid var(--border);border-radius:7px;background:#FAFBFC;padding:9px 8px;}
.calendar-summary strong{display:block;font-size:18px;color:var(--navy)!important;line-height:1.1;}
.calendar-summary span{font-size:9px;color:var(--muted)!important;text-transform:uppercase;letter-spacing:.25px;}
@media(max-width:900px){
  .calendar-day{min-height:46px;}
}
</style>
"""

MONTHS_RU = (
    "",
    "январь",
    "февраль",
    "март",
    "апрель",
    "май",
    "июнь",
    "июль",
    "август",
    "сентябрь",
    "октябрь",
    "ноябрь",
    "декабрь",
)
WEEKDAYS_RU = ("Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс")


def inject_calendar_css() -> None:
    st.markdown(CALENDAR_CSS, unsafe_allow_html=True)


def as_date(value: Any) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def effective_status(entry: dict[str, Any], today: date | None = None) -> str:
    """Return the operational status, automatically treating missed open deadlines as overdue."""
    today = today or date.today()
    stored = str(entry.get("status") or "planned")
    deadline = as_date(entry.get("deadline"))
    if stored != "done" and deadline and deadline < today:
        return "overdue"
    return stored


def status_matches(entry: dict[str, Any], status_filter: str) -> bool:
    return not status_filter or effective_status(entry) == status_filter


def month_start_for_week(week_id: str) -> date:
    year_text, week_text = week_id.split("-W", 1)
    monday = date.fromisocalendar(int(year_text), int(week_text), 1)
    return monday.replace(day=1)


def add_months(value: date, months: int) -> date:
    index = value.year * 12 + value.month - 1 + months
    return date(index // 12, index % 12 + 1, 1)


def two_month_period(month_start: date) -> tuple[date, date]:
    return month_start, add_months(month_start, 2) - timedelta(days=1)


def get_calendar_entries(
    department_id: str,
    period_start: date,
    period_end: date,
) -> list[dict[str, Any]]:
    """Load both deadlines and Chairman meeting dates with one database round-trip."""
    deadline_in_period = and_(
        weekly_entries.c.deadline.is_not(None),
        weekly_entries.c.deadline >= period_start,
        weekly_entries.c.deadline <= period_end,
    )
    meeting_in_period = and_(
        weekly_entries.c.is_major.is_(True),
        weekly_entries.c.meeting_date.is_not(None),
        weekly_entries.c.meeting_date >= period_start,
        weekly_entries.c.meeting_date <= period_end,
    )
    stmt = (
        select(weekly_entries)
        .where(
            weekly_entries.c.department_id == department_id,
            or_(deadline_in_period, meeting_in_period),
        )
        .order_by(weekly_entries.c.deadline, weekly_entries.c.meeting_date, weekly_entries.c.id)
    )
    return fetch_all(stmt)


def _calendar_events(entries: list[dict[str, Any]], status_filter: str) -> dict[date, list[dict[str, str]]]:
    events: dict[date, list[dict[str, str]]] = defaultdict(list)
    for entry in entries:
        if not status_matches(entry, status_filter):
            continue
        status = effective_status(entry)
        activity = html.escape(str(entry.get("activity") or "Без названия"))
        deadline = as_date(entry.get("deadline"))
        if deadline:
            events[deadline].append({"status": status, "title": activity, "kind": "deadline"})
        meeting_date = as_date(entry.get("meeting_date"))
        if bool(entry.get("is_major")) and meeting_date:
            events[meeting_date].append(
                {"status": "meeting", "title": f"Доклад: {activity}", "kind": "meeting"}
            )
    return events


def _render_month(month_start: date, events: dict[date, list[dict[str, str]]], selected_week_id: str) -> str:
    year, month = month_start.year, month_start.month
    selected_year, selected_week = (int(part) for part in selected_week_id.replace("W", "").split("-"))
    today = date.today()
    weeks = calendar.Calendar(firstweekday=0).monthdatescalendar(year, month)
    parts = [
        '<div class="month-calendar">',
        f'<div class="month-title">{MONTHS_RU[month]} {year}</div>',
        '<div class="calendar-grid">',
    ]
    parts.extend(f'<div class="calendar-weekday">{name}</div>' for name in WEEKDAYS_RU)

    for week in weeks:
        for day_value in week:
            classes = ["calendar-day"]
            if day_value.month != month:
                classes.append("other")
            if day_value.weekday() >= 5:
                classes.append("weekend")
            iso_year, iso_week, _ = day_value.isocalendar()
            if iso_year == selected_year and iso_week == selected_week:
                classes.append("in-week")
            if day_value == today:
                classes.append("today")
            day_events = events.get(day_value, [])
            dots = []
            for event in day_events[:4]:
                dots.append(
                    f'<span class="calendar-dot {event["status"]}" title="{event["title"]}"></span>'
                )
            if len(day_events) > 4:
                dots.append(f'<span class="calendar-more">+{len(day_events) - 4}</span>')
            parts.append(
                f'<div class="{" ".join(classes)}">'
                f'<div class="day-number">{day_value.day}</div>'
                f'<div class="calendar-dots">{"".join(dots)}</div>'
                '</div>'
            )
    parts.append('</div></div>')
    return "".join(parts)


def render_two_month_calendar(
    entries: list[dict[str, Any]],
    month_start: date,
    selected_week_id: str,
    status_filter: str = "",
) -> None:
    events = _calendar_events(entries, status_filter)
    html_block = (
        '<div class="calendar-card">'
        + _render_month(month_start, events, selected_week_id)
        + _render_month(add_months(month_start, 1), events, selected_week_id)
        + '</div>'
    )
    st.markdown(html_block, unsafe_allow_html=True)
    st.markdown(
        """
        <div class="calendar-legend">
          <span><i class="calendar-dot planned"></i>Запланировано</span>
          <span><i class="calendar-dot in_progress"></i>В работе</span>
          <span><i class="calendar-dot done"></i>Выполнено</span>
          <span><i class="calendar-dot risk"></i>Под риском</span>
          <span><i class="calendar-dot overdue"></i>Просрочено</span>
          <span><i class="calendar-dot meeting"></i>Доклад</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_calendar_summary(entries: list[dict[str, Any]], status_filter: str = "") -> None:
    filtered = [entry for entry in entries if status_matches(entry, status_filter)]
    overdue = sum(effective_status(entry) == "overdue" for entry in filtered)
    meetings = sum(bool(entry.get("is_major")) and as_date(entry.get("meeting_date")) is not None for entry in filtered)
    st.markdown(
        f"""
        <div class="calendar-summary">
          <div><strong>{len(filtered)}</strong><span>В периоде</span></div>
          <div><strong>{overdue}</strong><span>Просрочено</span></div>
          <div><strong>{meetings}</strong><span>Доклады</span></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_upcoming_tasks(
    entries: list[dict[str, Any]],
    status_filter: str = "",
    limit: int = 8,
) -> None:
    filtered = [entry for entry in entries if status_matches(entry, status_filter) and as_date(entry.get("deadline"))]
    filtered.sort(key=lambda entry: (as_date(entry.get("deadline")) or date.max, str(entry.get("activity") or "")))
    st.markdown('<div class="calendar-list"><div class="calendar-list-title">Ближайшие сроки</div>', unsafe_allow_html=True)
    if not filtered:
        st.markdown('<div class="small-note">В выбранном периоде задач с дедлайном нет.</div></div>', unsafe_allow_html=True)
        return
    parts = []
    for entry in filtered[:limit]:
        deadline = as_date(entry.get("deadline"))
        status = effective_status(entry)
        parts.append(
            '<div class="calendar-list-item">'
            f'<div class="calendar-list-date">{deadline:%d.%m}</div>'
            '<div class="calendar-list-body">'
            f'<b title="{html.escape(str(entry.get("activity") or ""))}">{html.escape(str(entry.get("activity") or "Без названия"))}</b>'
            f'<span>{html.escape(STATUS_LABELS.get(status, status))}</span>'
            '</div></div>'
        )
    if len(filtered) > limit:
        parts.append(f'<div class="small-note">Ещё задач: {len(filtered) - limit}</div>')
    st.markdown("".join(parts) + '</div>', unsafe_allow_html=True)


def status_options() -> list[str]:
    return [""] + list(STATUS_ORDER)


def status_label(value: str) -> str:
    return "Все статусы" if not value else STATUS_LABELS.get(value, value)
