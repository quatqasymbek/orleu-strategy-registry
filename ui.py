from __future__ import annotations

import html
from datetime import date, datetime, timedelta
from urllib.parse import urlencode

import streamlit as st

from reference_data import DEPARTMENT_BY_ID, STATUS_LABELS

CSS = r"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;500;600;700&display=swap');

:root{
  --navy:#002147;
  --navy-2:#0C3259;
  --blue:#25588A;
  --blue-2:#4C7399;
  --light-blue:#80A1C2;
  --yellow:#FFCA02;
  --page:#F6F8FB;
  --surface:#FFFFFF;
  --surface-soft:#F9FBFD;
  --text:#172536;
  --text-soft:#516174;
  --muted:#748397;
  --border:#DCE3EA;
  --border-strong:#C8D1DB;
  --success:#2F7F6E;
  --success-soft:#E9F5F1;
  --warning:#A96B00;
  --warning-soft:#FFF6DC;
  --danger:#B14A3A;
  --danger-soft:#FCEEEB;
  --info-soft:#EAF1F8;
}

html,body,.stApp,[data-testid="stAppViewContainer"]{
  font-family:'Roboto','Segoe UI',Arial,sans-serif!important;
  color:var(--text)!important;
  background:var(--page)!important;
  font-size:15px;
  line-height:1.45;
}
.stApp p,.stApp li,.stApp span,.stApp div{font-family:inherit;}
.stApp h1,.stApp h2,.stApp h3,.stApp h4,.stApp h5,.stApp h6{
  font-family:'Roboto','Segoe UI',Arial,sans-serif!important;
  color:var(--navy)!important;
  font-weight:700;
  letter-spacing:-.01em;
}
[data-testid="stHeader"]{background:transparent;height:0;}
[data-testid="stToolbar"],#MainMenu,footer,[data-testid="stDecoration"]{display:none!important;}
.block-container{max-width:1220px;padding:0 30px 64px 30px;}

/* Header */
.app-topbar{
  position:relative;
  background:var(--navy);
  color:#fff!important;
  margin-left:calc(-50vw + 50%);
  margin-right:calc(-50vw + 50%);
  padding:20px max(30px,calc((100vw - 1220px)/2 + 30px)) 0;
  border-top:4px solid var(--yellow);
  border-bottom:1px solid rgba(255,255,255,.10);
}
.app-topbar,.app-topbar *{color:#fff!important;}
.topbar-row{display:flex;align-items:flex-start;justify-content:space-between;gap:24px;flex-wrap:wrap;padding-bottom:18px;}
.brand{display:block;min-width:320px;}
.brand-accent{width:42px;height:4px;background:var(--yellow);border-radius:4px;margin:0 0 11px;}
.eyebrow{
  font-size:10.5px;
  letter-spacing:1.35px;
  text-transform:uppercase;
  color:#BFD0E0!important;
  margin-bottom:6px;
  font-weight:500;
}
.brand h1{font-size:21px!important;line-height:1.25;margin:0!important;color:#fff!important;font-weight:700!important;}
.brand-sub{font-size:12.5px;color:#C8D5E2!important;margin-top:6px;}
.top-right{display:flex;align-items:center;gap:10px;flex-wrap:wrap;justify-content:flex-end;}
.week-label{text-align:center;min-width:180px;}
.week-label .wk{font-size:13px;font-weight:700;letter-spacing:.2px;color:#fff!important;}
.week-label .rng{font-size:11px;color:#BFD0E0!important;margin-top:2px;}
.nav-link{
  display:inline-flex;align-items:center;justify-content:center;
  min-width:32px;height:32px;padding:0 10px;
  border:1px solid #406182;border-radius:6px;
  color:#fff!important;text-decoration:none;
  font-size:12px;font-weight:600;
  background:transparent;
  transition:.14s ease;
}
.nav-link:hover{background:var(--navy-2);border-color:#6D89A6;}
.user-badge{font-size:10.5px;color:#CBD7E3!important;text-align:right;line-height:1.4;max-width:245px;}
.mode-tabs{display:flex;gap:4px;}
.mode-tab{
  font-size:13px;font-weight:600;
  padding:10px 18px 11px;
  background:var(--navy-2);
  color:#C8D5E2!important;
  border-radius:7px 7px 0 0;
  text-decoration:none;
  position:relative;top:1px;
}
.mode-tab:hover{background:#153E68;color:#fff!important;}
.mode-tab.active{background:var(--page);color:var(--navy)!important;}
.page-pad{height:26px;}

/* Panels */
.panel-title{font-size:17px;font-weight:700;color:var(--navy)!important;margin:0 0 14px;line-height:1.3;}
.hint{font-size:13px;color:var(--muted)!important;}
[data-testid="stVerticalBlockBorderWrapper"]{
  background:var(--surface)!important;
  border:1px solid var(--border)!important;
  border-radius:10px!important;
  box-shadow:0 2px 8px rgba(0,33,71,.04)!important;
}
[data-testid="stVerticalBlockBorderWrapper"] p,
[data-testid="stVerticalBlockBorderWrapper"] span,
[data-testid="stVerticalBlockBorderWrapper"] div:not([role="option"]){color:var(--text);}
[data-testid="stMarkdownContainer"] p,[data-testid="stMarkdownContainer"] li{color:var(--text)!important;}
[data-testid="stCaptionContainer"] p,.stCaptionContainer p{color:var(--muted)!important;font-size:12.5px!important;}

/* Forms */
label,[data-testid="stWidgetLabel"] p{
  font-size:11.5px!important;
  text-transform:uppercase;
  letter-spacing:.42px;
  color:var(--blue)!important;
  font-weight:700!important;
}
.stTextInput input,.stDateInput input,.stTextArea textarea,[data-baseweb="select"]>div{
  background:#fff!important;
  border:1px solid var(--border-strong)!important;
  border-radius:7px!important;
  color:var(--text)!important;
  font-size:14px!important;
  box-shadow:none!important;
}
.stTextInput input:focus,.stDateInput input:focus,.stTextArea textarea:focus,[data-baseweb="select"]>div:focus-within{
  border-color:var(--blue)!important;
  box-shadow:0 0 0 2px rgba(37,88,138,.12)!important;
}
.stTextInput input::placeholder,.stTextArea textarea::placeholder{color:#8A98A8!important;opacity:1!important;}
[data-baseweb="select"] span,[data-baseweb="select"] input,[data-baseweb="select"] svg{color:var(--text)!important;fill:var(--text)!important;}
[data-baseweb="popover"],[role="listbox"]{background:#fff!important;color:var(--text)!important;}
[role="option"]{color:var(--text)!important;background:#fff!important;}
[role="option"]:hover{background:#F0F5FA!important;}
[data-testid="stCheckbox"] label p{color:var(--text-soft)!important;text-transform:none!important;font-size:13px!important;letter-spacing:0!important;}

/* Buttons */
.stButton>button,.stFormSubmitButton>button,.stDownloadButton>button{
  font-family:inherit!important;
  font-weight:600;
  font-size:13.5px;
  border-radius:7px;
  border:1px solid var(--blue);
  background:var(--blue);
  color:#fff!important;
  padding:.58rem 1.05rem;
  box-shadow:none;
  transition:.14s ease;
}
.stButton>button p,.stFormSubmitButton>button p,.stDownloadButton>button p{color:inherit!important;}
.stButton>button:hover,.stFormSubmitButton>button:hover,.stDownloadButton>button:hover{
  background:var(--navy-2);
  border-color:var(--navy-2);
  color:#fff!important;
}
.stButton>button[kind="secondary"]{
  background:#fff;
  color:var(--navy)!important;
  border-color:var(--border-strong);
}
.stButton>button[kind="secondary"]:hover{
  background:#F2F6FA;
  border-color:var(--blue-2);
  color:var(--navy)!important;
}

/* Login */
.login-shell{max-width:620px;margin:8vh auto 1rem;}
.login-card{background:#fff;border:1px solid var(--border);border-radius:12px;padding:34px;box-shadow:0 12px 32px rgba(0,33,71,.08);}
.login-eyebrow{font-size:11px;letter-spacing:1.2px;color:var(--blue)!important;font-weight:700;}
.login-title{font-size:34px;font-weight:700;line-height:1.15;margin:23px 0 14px;color:var(--navy)!important;}
.login-sub{font-size:15px;color:var(--text-soft)!important;}

/* Alerts and entries */
.banner{display:flex;background:var(--warning-soft);border:1px solid #E6BE68;border-radius:9px;padding:15px 18px;margin-bottom:18px;align-items:center;gap:12px;}
.banner-dot{width:36px;height:36px;border-radius:50%;border:2px solid var(--warning);display:flex;align-items:center;justify-content:center;font-size:9.5px;font-weight:700;color:var(--warning)!important;flex-shrink:0;}
.banner b{display:block;font-size:14px;color:#704900!important;}.banner span{font-size:12.5px;color:#795F2B!important;}
.entry{border:1px solid var(--border);border-radius:9px;padding:15px 17px;background:#fff;margin-bottom:10px;}
.entry-num{font-size:10.5px;color:var(--muted)!important;background:#EEF2F6;border-radius:4px;padding:3px 7px;}
.entry-task{font-size:12px;color:var(--blue)!important;font-weight:700;margin-top:6px;}
.entry-activity{font-size:14.5px;font-weight:600;color:var(--text)!important;margin:6px 0 9px;}
.entry-meta{display:flex;gap:15px;flex-wrap:wrap;font-size:12.5px;color:var(--text-soft)!important;}
.entry-meta span,.entry-meta b{color:var(--text-soft)!important;}

.stamp{display:inline-flex;align-items:center;gap:5px;font-size:10px;font-weight:700;letter-spacing:.35px;text-transform:uppercase;padding:4px 9px;border-radius:16px;border:1px solid;}
.stamp::before{content:'';width:6px;height:6px;border-radius:50%;display:inline-block;}
.stamp.planned{color:#5E6975!important;border-color:#AAB4BF;background:#F4F6F8;}.stamp.planned::before{background:#7F8B97;}
.stamp.in_progress{color:#25588A!important;border-color:#91ADC8;background:var(--info-soft);}.stamp.in_progress::before{background:var(--blue);}
.stamp.done{color:#256A5A!important;border-color:#8CB8AC;background:var(--success-soft);}.stamp.done::before{background:var(--success);}
.stamp.risk{color:#855500!important;border-color:#DDB866;background:var(--warning-soft);}.stamp.risk::before{background:var(--warning);}
.stamp.overdue{color:#953C31!important;border-color:#D89C94;background:var(--danger-soft);}.stamp.overdue::before{background:var(--danger);}
.major-flag{font-size:10px;letter-spacing:.35px;color:var(--danger)!important;border:1px solid #D89C94;background:var(--danger-soft);border-radius:4px;padding:3px 6px;text-transform:uppercase;font-weight:700;}

/* Dashboard */
.stat-strip{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin-bottom:18px;}
.stat-card{background:#fff;border:1px solid var(--border);border-radius:9px;padding:16px 17px;}
.stat-card .n{font-size:28px;font-weight:700;color:var(--navy)!important;line-height:1.1;}
.stat-card .l{font-size:11px;color:var(--muted)!important;text-transform:uppercase;letter-spacing:.4px;margin-top:6px;font-weight:600;}
.acc-done .n{color:var(--success)!important;}.acc-progress .n{color:var(--blue)!important;}.acc-risk .n{color:var(--warning)!important;}.acc-major .n{color:var(--danger)!important;}
.block-title{font-size:13px;font-weight:700;text-transform:uppercase;letter-spacing:.55px;color:var(--navy)!important;padding-bottom:8px;margin:22px 0 8px;border-bottom:2px solid var(--yellow);}
.dept-row{padding:13px 4px;border-bottom:1px solid var(--border);}
.dept-head{display:flex;align-items:flex-start;justify-content:space-between;gap:10px;}
.dept-name{font-size:13.5px;font-weight:700;color:var(--navy)!important;}
.dept-updated{font-size:10.5px;color:var(--muted)!important;}
.dept-updated.stale{color:var(--danger)!important;}
.mini-entry{display:flex;align-items:center;gap:9px;font-size:13px;padding:7px 0;border-top:1px dotted var(--border);color:var(--text)!important;}
.mini-entry .txt{flex:1;color:var(--text)!important;}.mini-entry .dl{font-size:11px;color:var(--muted)!important;white-space:nowrap;}
.no-report{font-size:12.5px;color:var(--muted)!important;font-style:italic;padding:10px 4px;}
.timeline-item{display:flex;gap:15px;padding:13px 0;border-top:1px solid var(--border);}
.timeline-date{font-size:12px;font-weight:700;color:var(--danger)!important;min-width:110px;}
.timeline-body b{display:block;font-size:13.5px;color:var(--navy)!important;}.timeline-body span{font-size:12.5px;color:var(--text-soft)!important;}
.small-note{font-size:11px;color:var(--muted)!important;}
.empty-note{text-align:center;padding:28px 12px;color:var(--muted)!important;font-size:13px;border:1px dashed var(--border-strong);border-radius:8px;background:var(--surface-soft);}
.admin-note{background:#EEF4F9;border-left:3px solid var(--blue);padding:11px 13px;font-size:12.5px;color:var(--text-soft)!important;border-radius:4px;margin-bottom:12px;}

[data-testid="stExpander"]{background:#fff;border:1px solid var(--border)!important;border-radius:9px!important;}
[data-testid="stExpander"] summary p{color:var(--navy)!important;font-weight:700!important;}
[data-testid="stAlert"] p{color:var(--text)!important;}

@media(max-width:900px){
  .block-container{padding:0 18px 48px;}
  .app-topbar{padding-left:20px;padding-right:20px;}
  .stat-strip{grid-template-columns:repeat(2,1fr);}
  .top-right{justify-content:flex-start;}
  .week-label{min-width:145px;}
}
@media(max-width:560px){
  .brand{min-width:0;}
  .brand h1{font-size:18px!important;}
  .brand-sub{font-size:11.5px;}
  .mode-tab{padding:9px 12px;font-size:12px;}
  .stat-strip{grid-template-columns:1fr 1fr;}
  .stat-card{padding:13px;}
  .stat-card .n{font-size:24px;}
}
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
              <div class="brand-accent"></div>
              <div class="eyebrow">Стратегия развития 2025–2029 · План на 2026 год</div>
              <h1>Реестр еженедельного исполнения</h1>
              <div class="brand-sub">4 направления · 17 задач · 84 показателя — по подразделениям</div>
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
