from __future__ import annotations

import html
from datetime import date, datetime, timedelta
from urllib.parse import urlencode

import streamlit as st

from reference_data import DEPARTMENT_BY_ID, STATUS_LABELS

CSS = r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500;600&family=IBM+Plex+Sans:ital,wght@0,400;0,500;0,600;0,700;1,400&display=swap');
:root{
  --ink:#12213A;--ink-soft:#2E3E5C;--paper:#F1EFE8;--paper-raise:#FAF9F5;
  --line:#D8D3C4;--line-soft:#E5E1D5;--amber:#C8842A;--amber-soft:#F3E1C2;
  --teal:#2F7F6E;--teal-soft:#D9EBE6;--rust:#B04A32;--rust-soft:#F1DBD3;
  --slate:#4C6C9B;--slate-soft:#DEE6F1;--gray:#8A8577;
}
html,body,[class*="css"]{font-family:'IBM Plex Sans',sans-serif;color:var(--ink);}
.stApp{background:var(--paper);}
[data-testid="stHeader"]{background:transparent;height:0;}
[data-testid="stToolbar"],#MainMenu,footer,[data-testid="stDecoration"]{display:none!important;}
.block-container{max-width:1180px;padding:0 28px 60px 28px;}
.app-topbar{background:var(--ink);color:var(--paper-raise);margin-left:calc(-50vw + 50%);margin-right:calc(-50vw + 50%);padding:18px max(28px,calc((100vw - 1180px)/2 + 28px)) 0;}
.topbar-row{display:flex;align-items:flex-start;justify-content:space-between;gap:20px;flex-wrap:wrap;padding-bottom:16px;}
.brand{display:flex;align-items:center;gap:14px;}.brand-seal{width:44px;height:44px;border:1.5px solid var(--amber);border-radius:50%;display:flex;align-items:center;justify-content:center;font-family:'IBM Plex Mono';font-size:10px;letter-spacing:.5px;color:var(--amber);text-align:center;line-height:1.1;flex-shrink:0;transform:rotate(-6deg);}
.eyebrow{font-family:'IBM Plex Mono';font-size:10.5px;letter-spacing:1.5px;text-transform:uppercase;color:#9FB0CC;margin-bottom:3px;}.brand h1{font-family:'Space Grotesk';font-weight:600;font-size:19px;margin:0;letter-spacing:.2px}.brand-sub{font-size:12px;color:#B7C2D9;margin-top:2px}.top-right{display:flex;align-items:center;gap:10px;flex-wrap:wrap;justify-content:flex-end}.week-label{text-align:center;min-width:190px;font-family:'IBM Plex Mono'}.week-label .wk{font-size:13px;font-weight:600;letter-spacing:.5px}.week-label .rng{font-size:11px;color:#9FB0CC;margin-top:1px}.nav-link{display:inline-flex;align-items:center;justify-content:center;min-width:30px;height:30px;padding:0 9px;border:1px solid #3A4D71;border-radius:6px;color:var(--paper-raise)!important;text-decoration:none;font-family:'IBM Plex Mono';font-size:12px}.nav-link:hover{background:#22345A}.user-badge{font-family:'IBM Plex Mono';font-size:10px;color:#B7C2D9;text-align:right}.mode-tabs{display:flex;gap:4px}.mode-tab{font-family:'Space Grotesk';font-size:12.5px;font-weight:600;letter-spacing:.3px;padding:9px 18px 11px;background:#1B2C4C;color:#9FB0CC!important;border-radius:8px 8px 0 0;text-decoration:none;position:relative;top:1px}.mode-tab.active{background:var(--paper);color:var(--ink)!important}
.page-pad{height:24px}.panel-title{font-family:'Space Grotesk';font-size:15.5px;font-weight:600;margin:0 0 14px}.hint{font-size:12px;color:var(--gray)}
[data-testid="stVerticalBlockBorderWrapper"]{background:var(--paper-raise);border-color:var(--line)!important;border-radius:10px!important;box-shadow:none!important;}
label,[data-testid="stWidgetLabel"] p{font-size:11px!important;text-transform:uppercase;letter-spacing:.5px;color:var(--gray)!important;font-weight:600!important}
.stTextInput input,.stDateInput input,.stTextArea textarea,[data-baseweb="select"]>div{background:#fff!important;border-color:var(--line)!important;border-radius:7px!important;color:var(--ink)!important;font-size:13.5px!important}
.stButton>button,.stFormSubmitButton>button,.stDownloadButton>button{font-family:'Space Grotesk';font-weight:600;font-size:13px;border-radius:7px;border:1px solid var(--ink);background:var(--ink);color:var(--paper-raise);padding:.55rem 1rem}.stButton>button:hover,.stFormSubmitButton>button:hover{border-color:var(--ink);color:white;opacity:.86}.stButton>button[kind="secondary"]{background:transparent;color:var(--ink);border-color:var(--line)}
.login-shell{max-width:620px;margin:9vh auto 1rem}.login-card{background:var(--paper-raise);border:1px solid var(--line);border-radius:14px;padding:32px;box-shadow:0 14px 40px rgba(18,33,58,.09)}.login-eyebrow{font-family:'IBM Plex Mono';font-size:11px;letter-spacing:1.4px;color:var(--slate);font-weight:600}.login-title{font-family:'Space Grotesk';font-size:34px;font-weight:700;line-height:1.15;margin:24px 0 14px}.login-sub{font-size:15px;color:#5d708a}
.banner{display:flex;background:var(--amber-soft);border:1px solid var(--amber);border-radius:10px;padding:14px 18px;margin-bottom:18px;align-items:center;gap:12px}.banner-dot{width:34px;height:34px;border-radius:50%;border:2px dashed var(--amber);display:flex;align-items:center;justify-content:center;font-family:'IBM Plex Mono';font-size:10px;font-weight:600;color:var(--amber);flex-shrink:0}.banner b{display:block;font-family:'Space Grotesk';font-size:13.5px}.banner span{font-size:12px;color:var(--ink-soft)}
.entry{border:1px solid var(--line-soft);border-radius:9px;padding:14px 16px;background:#fff}.entry-num{font-family:'IBM Plex Mono';font-size:11px;color:var(--gray);background:var(--line-soft);border-radius:5px;padding:2px 7px}.entry-task{font-size:11.5px;color:var(--slate);font-weight:600;margin-top:5px}.entry-activity{font-size:14px;font-weight:500;margin:5px 0 8px}.entry-meta{display:flex;gap:14px;flex-wrap:wrap;font-size:12px;color:var(--ink-soft)}.stamp{display:inline-flex;align-items:center;gap:5px;font-family:'IBM Plex Mono';font-size:10px;font-weight:600;letter-spacing:.4px;text-transform:uppercase;padding:3px 9px 3px 7px;border-radius:20px;border:1.5px dashed;transform:rotate(-1.2deg)}.stamp::before{content:'';width:6px;height:6px;border-radius:50%;display:inline-block}.stamp.planned{color:var(--gray);border-color:var(--gray);background:#F3F2ED}.stamp.planned::before{background:var(--gray)}.stamp.in_progress{color:var(--slate);border-color:var(--slate);background:var(--slate-soft)}.stamp.in_progress::before{background:var(--slate)}.stamp.done{color:var(--teal);border-color:var(--teal);background:var(--teal-soft)}.stamp.done::before{background:var(--teal)}.stamp.risk{color:var(--amber);border-color:var(--amber);background:var(--amber-soft)}.stamp.risk::before{background:var(--amber)}.stamp.overdue{color:var(--rust);border-color:var(--rust);background:var(--rust-soft)}.stamp.overdue::before{background:var(--rust)}.major-flag{font-family:'IBM Plex Mono';font-size:10px;letter-spacing:.4px;color:var(--rust);border:1px solid var(--rust);border-radius:5px;padding:2px 6px;text-transform:uppercase}
.stat-strip{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin-bottom:18px}.stat-card{background:var(--paper-raise);border:1px solid var(--line);border-radius:10px;padding:14px 16px}.stat-card .n{font-family:'Space Grotesk';font-size:26px;font-weight:700}.stat-card .l{font-size:11px;color:var(--gray);text-transform:uppercase;letter-spacing:.4px;margin-top:2px}.acc-done .n{color:var(--teal)}.acc-progress .n{color:var(--slate)}.acc-risk .n{color:var(--amber)}.acc-major .n{color:var(--rust)}
.block-title{font-family:'Space Grotesk';font-size:12.5px;font-weight:600;text-transform:uppercase;letter-spacing:.6px;color:var(--ink-soft);padding-bottom:6px;margin:20px 0 8px;border-bottom:1px solid var(--line)}.dept-row{padding:10px 4px;border-bottom:1px solid var(--line-soft)}.dept-head{display:flex;align-items:flex-start;justify-content:space-between;gap:10px}.dept-name{font-size:13px;font-weight:600}.dept-updated{font-family:'IBM Plex Mono';font-size:10.5px;color:var(--gray)}.dept-updated.stale{color:var(--rust)}.mini-entry{display:flex;align-items:center;gap:8px;font-size:12.5px;padding:5px 0;border-top:1px dotted var(--line-soft)}.mini-entry .txt{flex:1}.mini-entry .dl{font-family:'IBM Plex Mono';font-size:11px;color:var(--gray);white-space:nowrap}.no-report{font-size:12px;color:var(--gray);font-style:italic;padding:10px 4px}.timeline-item{display:flex;gap:14px;padding:12px 0;border-top:1px solid var(--line-soft)}.timeline-date{font-family:'IBM Plex Mono';font-size:12px;font-weight:600;color:var(--rust);min-width:110px}.timeline-body b{display:block;font-size:13px}.timeline-body span{font-size:12px;color:var(--ink-soft)}
.small-note{font-size:11px;color:var(--gray);font-family:'IBM Plex Mono'}.empty-note{text-align:center;padding:26px 10px;color:var(--gray);font-size:13px;border:1px dashed var(--line);border-radius:9px}.admin-note{background:#eef3f8;border-left:3px solid var(--slate);padding:10px 12px;font-size:12px;color:var(--ink-soft);border-radius:4px}
@media(max-width:760px){.block-container{padding:0 12px 40px}.app-topbar{padding-left:16px;padding-right:16px}.stat-strip{grid-template-columns:repeat(2,1fr)}.top-right{justify-content:flex-start}.week-label{min-width:140px}}
</style>
"""


def inject_css() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def week_id_from_date(value: date) -> str:
    year, week, _ = value.isocalendar()
    return f"{year}-W{week:02d}"


def current_week_id() -> str:
    return week_id_from_date(date.today())


def parse_week_id(week_id: str) -> tuple[int, int]:
    year_text, week_text = week_id.split("-W")
    return int(year_text), int(week_text)


def monday_for_week(week_id: str) -> date:
    year, week = parse_week_id(week_id)
    return date.fromisocalendar(year, week, 1)


def shift_week(week_id: str, delta: int) -> str:
    return week_id_from_date(monday_for_week(week_id) + timedelta(days=delta * 7))


def week_range_label(week_id: str) -> str:
    months = ["", "января", "февраля", "марта", "апреля", "мая", "июня", "июля", "августа", "сентября", "октября", "ноября", "декабря"]
    monday = monday_for_week(week_id)
    sunday = monday + timedelta(days=6)
    if monday.month == sunday.month:
        return f"{monday.day:02d}–{sunday.day:02d} {months[sunday.month]} {sunday.year}"
    return f"{monday.day:02d} {months[monday.month]} – {sunday.day:02d} {months[sunday.month]} {sunday.year}"


def fmt_date(value) -> str:
    if not value:
        return "—"
    if isinstance(value, str):
        try:
            value = date.fromisoformat(value)
        except ValueError:
            return value
    return value.strftime("%d.%m.%Y")


def fmt_updated(value) -> str:
    if not value:
        return ""
    if isinstance(value, str):
        try:
            value = datetime.fromisoformat(value)
        except ValueError:
            return value
    return value.astimezone().strftime("%d.%m, %H:%M") if value.tzinfo else value.strftime("%d.%m, %H:%M")


def safe(text) -> str:
    return html.escape("" if text is None else str(text))


def query_link(**params) -> str:
    return "?" + urlencode({key: value for key, value in params.items() if value is not None})


def render_header(user: dict, week_id: str, mode: str) -> None:
    year, week = parse_week_id(week_id)
    prev_week = shift_week(week_id, -1)
    next_week = shift_week(week_id, 1)
    allowed_dept = user["role"] in {"department", "strategy_admin"}
    allowed_lead = user["role"] in {"chairman", "strategy_admin"}
    tabs = []
    if allowed_dept:
        tabs.append(f'<a class="mode-tab {"active" if mode == "dept" else ""}" href="{query_link(week=week_id, mode="dept")}">Кабинет департамента</a>')
    if allowed_lead:
        tabs.append(f'<a class="mode-tab {"active" if mode == "lead" else ""}" href="{query_link(week=week_id, mode="lead")}">Свод руководителя</a>')
    st.markdown(
        f"""
        <div class="app-topbar">
          <div class="topbar-row">
            <div class="brand">
              <div class="brand-seal">ӨРЛЕУ<br>1.06→</div>
              <div>
                <div class="eyebrow">Стратегия развития 2025–2029 · План на 2026 год</div>
                <h1>Реестр еженедельного исполнения</h1>
                <div class="brand-sub">4 направления · 17 задач · 84 показателя — по департаментам</div>
              </div>
            </div>
            <div class="top-right">
              <a class="nav-link" href="{query_link(week=prev_week, mode=mode)}">‹</a>
              <div class="week-label"><div class="wk">Неделя {week}, {year}</div><div class="rng">{week_range_label(week_id)}</div></div>
              <a class="nav-link" href="{query_link(week=next_week, mode=mode)}">›</a>
              <a class="nav-link" href="{query_link(week=current_week_id(), mode=mode)}">СЕЙЧАС</a>
              <div class="user-badge">{safe(user['username'])}<br>{safe(user['display_name'])}</div>
              <a class="nav-link" href="{query_link(logout='1')}">ВЫЙТИ</a>
            </div>
          </div>
          <div class="mode-tabs">{''.join(tabs)}</div>
        </div><div class="page-pad"></div>
        """,
        unsafe_allow_html=True,
    )


def status_stamp(status: str) -> str:
    return f'<span class="stamp {safe(status)}">{safe(STATUS_LABELS.get(status, status))}</span>'


def department_name(department_id: str) -> str:
    return DEPARTMENT_BY_ID.get(department_id, {"name": department_id})["name"]
