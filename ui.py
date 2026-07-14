from __future__ import annotations

import html
from datetime import date, datetime, timedelta
from urllib.parse import urlencode

import streamlit as st

from reference_data import DEPARTMENT_BY_ID, STATUS_LABELS

CSS = r"""
<style>
:root{
  --navy:#102A43;
  --navy-2:#173F6C;
  --blue:#2563A6;
  --blue-hover:#1D4E89;
  --page:#F4F7FB;
  --surface:#FFFFFF;
  --surface-soft:#F8FAFC;
  --text:#1C2B3A;
  --text-soft:#506176;
  --muted:#6B7C8F;
  --border:#D9E2EC;
  --border-strong:#C5D0DD;
  --amber:#B76E00;
  --amber-soft:#FFF4DB;
  --teal:#147D64;
  --teal-soft:#E9F7F2;
  --rust:#B63B32;
  --rust-soft:#FDECE9;
  --slate:#2F64A3;
  --slate-soft:#EAF2FB;
  --shadow:0 6px 18px rgba(16,42,67,.07);
}

html,body,.stApp,[data-testid="stAppViewContainer"]{
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif!important;
  color:var(--text)!important;
  background:var(--page)!important;
  font-size:15px;
  line-height:1.45;
}
.stApp p,.stApp li,.stApp span,.stApp div{font-family:inherit;}
.stApp h1,.stApp h2,.stApp h3,.stApp h4,.stApp h5,.stApp h6{
  color:var(--navy)!important;
  font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Arial,sans-serif!important;
  font-weight:700;
  letter-spacing:-.01em;
}
[data-testid="stHeader"]{background:transparent;height:0;}
[data-testid="stToolbar"],#MainMenu,footer,[data-testid="stDecoration"]{display:none!important;}
.block-container{max-width:1220px;padding:0 30px 64px 30px;}

/* Header */
.app-topbar{
  background:linear-gradient(135deg,var(--navy) 0%,#142F50 100%);
  color:#F7FAFC!important;
  margin-left:calc(-50vw + 50%);
  margin-right:calc(-50vw + 50%);
  padding:20px max(30px,calc((100vw - 1220px)/2 + 30px)) 0;
  border-bottom:1px solid rgba(255,255,255,.08);
  box-shadow:0 4px 14px rgba(16,42,67,.12);
}
.app-topbar,.app-topbar *{color:#F7FAFC!important;}
.topbar-row{display:flex;align-items:flex-start;justify-content:space-between;gap:22px;flex-wrap:wrap;padding-bottom:18px;}
.brand{display:flex;align-items:center;gap:15px;}
.brand-seal{
  width:48px;height:48px;border:1.5px solid #E6A13A;border-radius:50%;
  display:flex;align-items:center;justify-content:center;
  font-family:ui-monospace,SFMono-Regular,Consolas,"Liberation Mono",monospace!important;
  font-size:10px;letter-spacing:.55px;color:#F2AD3F!important;text-align:center;line-height:1.1;
  flex-shrink:0;transform:rotate(-5deg);background:rgba(255,255,255,.02);
}
.eyebrow{
  font-family:ui-monospace,SFMono-Regular,Consolas,"Liberation Mono",monospace!important;
  font-size:10.5px;letter-spacing:1.35px;text-transform:uppercase;color:#B7C9DE!important;margin-bottom:5px;
}
.brand h1{font-size:21px!important;line-height:1.25;margin:0!important;color:#FFFFFF!important;font-weight:700!important;}
.brand-sub{font-size:12.5px;color:#C4D2E3!important;margin-top:5px;}
.top-right{display:flex;align-items:center;gap:10px;flex-wrap:wrap;justify-content:flex-end;}
.week-label{text-align:center;min-width:190px;font-family:ui-monospace,SFMono-Regular,Consolas,"Liberation Mono",monospace!important;}
.week-label .wk{font-size:13px;font-weight:700;letter-spacing:.35px;color:#FFFFFF!important;}
.week-label .rng{font-size:11px;color:#B7C9DE!important;margin-top:2px;}
.nav-link{
  display:inline-flex;align-items:center;justify-content:center;min-width:32px;height:32px;padding:0 10px;
  border:1px solid #49617F;border-radius:7px;color:#FFFFFF!important;text-decoration:none;
  font-size:12px;font-weight:650;background:rgba(255,255,255,.025);transition:.15s ease;
}
.nav-link:hover{background:#24476E;border-color:#6D87A6;transform:translateY(-1px);}
.user-badge{font-size:10.5px;color:#C4D2E3!important;text-align:right;line-height:1.35;}
.mode-tabs{display:flex;gap:6px;}
.mode-tab{
  font-size:13px;font-weight:650;padding:10px 18px 12px;background:#1B385C;color:#C2D2E5!important;
  border-radius:8px 8px 0 0;text-decoration:none;position:relative;top:1px;transition:.15s ease;
}
.mode-tab:hover{background:#23476F;color:#FFFFFF!important;}
.mode-tab.active{background:var(--page);color:var(--navy)!important;}
.page-pad{height:26px;}

/* Cards and general text */
.panel-title{font-size:17px;font-weight:700;color:var(--navy)!important;margin:0 0 14px;line-height:1.3;}
.hint{font-size:13px;color:var(--muted)!important;}
[data-testid="stVerticalBlockBorderWrapper"]{
  background:var(--surface)!important;border:1px solid var(--border)!important;border-radius:12px!important;
  box-shadow:var(--shadow)!important;
}
[data-testid="stVerticalBlockBorderWrapper"] p,
[data-testid="stVerticalBlockBorderWrapper"] span,
[data-testid="stVerticalBlockBorderWrapper"] div:not([role="option"]){color:var(--text);}
[data-testid="stMarkdownContainer"] p,[data-testid="stMarkdownContainer"] li{color:var(--text)!important;}
[data-testid="stCaptionContainer"] p,.stCaptionContainer p{color:var(--muted)!important;font-size:12.5px!important;}

/* Form labels and controls */
label,[data-testid="stWidgetLabel"] p{
  font-size:11.5px!important;text-transform:uppercase;letter-spacing:.45px;color:var(--text-soft)!important;font-weight:700!important;
}
.stTextInput input,.stDateInput input,.stTextArea textarea,
[data-baseweb="select"]>div{
  background:#FFFFFF!important;border:1px solid var(--border-strong)!important;border-radius:8px!important;
  color:var(--text)!important;font-size:14px!important;box-shadow:none!important;
}
.stTextInput input:focus,.stDateInput input:focus,.stTextArea textarea:focus,
[data-baseweb="select"]>div:focus-within{
  border-color:var(--blue)!important;box-shadow:0 0 0 2px rgba(37,99,166,.14)!important;
}
.stTextInput input::placeholder,.stTextArea textarea::placeholder{color:#8795A6!important;opacity:1!important;}
[data-baseweb="select"] span,[data-baseweb="select"] input,[data-baseweb="select"] svg{color:var(--text)!important;fill:var(--text)!important;}
[data-baseweb="popover"],[role="listbox"]{background:#FFFFFF!important;color:var(--text)!important;}
[role="option"]{color:var(--text)!important;background:#FFFFFF!important;}
[role="option"]:hover{background:#EEF4FA!important;}
[data-testid="stCheckbox"] label p{color:var(--text-soft)!important;text-transform:none!important;font-size:13px!important;letter-spacing:0!important;}

/* Buttons */
.stButton>button,.stFormSubmitButton>button,.stDownloadButton>button{
  font-family:inherit!important;font-weight:650;font-size:13.5px;border-radius:8px;
  border:1px solid var(--blue);background:var(--blue);color:#FFFFFF!important;
  padding:.58rem 1.05rem;box-shadow:0 2px 5px rgba(37,99,166,.13);transition:.15s ease;
}
.stButton>button p,.stFormSubmitButton>button p,.stDownloadButton>button p{color:inherit!important;}
.stButton>button:hover,.stFormSubmitButton>button:hover,.stDownloadButton>button:hover{
  border-color:var(--blue-hover);background:var(--blue-hover);color:#FFFFFF!important;transform:translateY(-1px);
}
.stButton>button[kind="secondary"]{
  background:#FFFFFF;color:var(--navy)!important;border-color:var(--border-strong);box-shadow:none;
}
.stButton>button[kind="secondary"]:hover{background:#F3F7FB;border-color:#8EA2B8;color:var(--navy)!important;}

/* Login */
.login-shell{max-width:620px;margin:8vh auto 1rem;}
.login-card{background:var(--surface);border:1px solid var(--border);border-radius:16px;padding:34px;box-shadow:0 16px 42px rgba(16,42,67,.10);}
.login-eyebrow{font-size:11px;letter-spacing:1.25px;color:var(--slate)!important;font-weight:700;}
.login-title{font-size:34px;font-weight:750;line-height:1.15;margin:23px 0 14px;color:var(--navy)!important;}
.login-sub{font-size:15px;color:var(--text-soft)!important;}

/* Alerts and entries */
.banner{display:flex;background:var(--amber-soft);border:1px solid #E5B45D;border-radius:11px;padding:15px 18px;margin-bottom:18px;align-items:center;gap:12px;}
.banner-dot{width:36px;height:36px;border-radius:50%;border:2px dashed var(--amber);display:flex;align-items:center;justify-content:center;font-size:9.5px;font-weight:700;color:var(--amber)!important;flex-shrink:0;}
.banner b{display:block;font-size:14px;color:#6E4600!important;}.banner span{font-size:12.5px;color:#775B24!important;}
.entry{border:1px solid var(--border);border-radius:10px;padding:15px 17px;background:#FFFFFF;margin-bottom:10px;box-shadow:0 2px 7px rgba(16,42,67,.035);}
.entry-num{font-family:ui-monospace,SFMono-Regular,Consolas,"Liberation Mono",monospace!important;font-size:10.5px;color:var(--muted)!important;background:#EEF2F6;border-radius:5px;padding:3px 7px;}
.entry-task{font-size:12px;color:var(--slate)!important;font-weight:700;margin-top:6px;}
.entry-activity{font-size:14.5px;font-weight:650;color:var(--text)!important;margin:6px 0 9px;}
.entry-meta{display:flex;gap:15px;flex-wrap:wrap;font-size:12.5px;color:var(--text-soft)!important;}
.entry-meta span,.entry-meta b{color:var(--text-soft)!important;}

.stamp{display:inline-flex;align-items:center;gap:5px;font-size:10px;font-weight:700;letter-spacing:.35px;text-transform:uppercase;padding:4px 9px;border-radius:18px;border:1px solid;}
.stamp::before{content:'';width:6px;height:6px;border-radius:50%;display:inline-block;}
.stamp.planned{color:#5C6775!important;border-color:#AAB4C0;background:#F3F5F7;}.stamp.planned::before{background:#7A8795;}
.stamp.in_progress{color:#24578E!important;border-color:#88A8CB;background:var(--slate-soft);}.stamp.in_progress::before{background:var(--slate);}
.stamp.done{color:#0D6B55!important;border-color:#79B9A8;background:var(--teal-soft);}.stamp.done::before{background:var(--teal);}
.stamp.risk{color:#8D5600!important;border-color:#E0B35F;background:var(--amber-soft);}.stamp.risk::before{background:var(--amber);}
.stamp.overdue{color:#9C3029!important;border-color:#D99B95;background:var(--rust-soft);}.stamp.overdue::before{background:var(--rust);}
.major-flag{font-size:10px;letter-spacing:.35px;color:var(--rust)!important;border:1px solid #D99B95;background:var(--rust-soft);border-radius:5px;padding:3px 6px;text-transform:uppercase;font-weight:700;}

/* Dashboard */
.stat-strip{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin-bottom:18px;}
.stat-card{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:16px 17px;box-shadow:var(--shadow);}
.stat-card .n{font-size:28px;font-weight:750;color:var(--navy)!important;line-height:1.1;}
.stat-card .l{font-size:11px;color:var(--muted)!important;text-transform:uppercase;letter-spacing:.4px;margin-top:6px;font-weight:650;}
.acc-done .n{color:var(--teal)!important;}.acc-progress .n{color:var(--slate)!important;}.acc-risk .n{color:var(--amber)!important;}.acc-major .n{color:var(--rust)!important;}
.block-title{font-size:13px;font-weight:750;text-transform:uppercase;letter-spacing:.55px;color:var(--navy)!important;padding-bottom:8px;margin:22px 0 8px;border-bottom:1px solid var(--border-strong);}
.dept-row{padding:13px 4px;border-bottom:1px solid var(--border);}
.dept-head{display:flex;align-items:flex-start;justify-content:space-between;gap:10px;}
.dept-name{font-size:13.5px;font-weight:700;color:var(--navy)!important;}
.dept-updated{font-family:ui-monospace,SFMono-Regular,Consolas,"Liberation Mono",monospace!important;font-size:10.5px;color:var(--muted)!important;}
.dept-updated.stale{color:var(--rust)!important;}
.mini-entry{display:flex;align-items:center;gap:9px;font-size:13px;padding:7px 0;border-top:1px dotted var(--border);color:var(--text)!important;}
.mini-entry .txt{flex:1;color:var(--text)!important;}.mini-entry .dl{font-size:11px;color:var(--muted)!important;white-space:nowrap;}
.no-report{font-size:12.5px;color:var(--muted)!important;font-style:italic;padding:10px 4px;}
.timeline-item{display:flex;gap:15px;padding:13px 0;border-top:1px solid var(--border);}
.timeline-date{font-size:12px;font-weight:700;color:var(--rust)!important;min-width:110px;}
.timeline-body b{display:block;font-size:13.5px;color:var(--navy)!important;}.timeline-body span{font-size:12.5px;color:var(--text-soft)!important;}
.small-note{font-size:11px;color:var(--muted)!important;}
.empty-note{text-align:center;padding:28px 12px;color:var(--muted)!important;font-size:13px;border:1px dashed var(--border-strong);border-radius:10px;background:var(--surface-soft);}
.admin-note{background:#EDF4FA;border-left:4px solid var(--slate);padding:11px 13px;font-size:12.5px;color:var(--text-soft)!important;border-radius:5px;margin-bottom:12px;}

/* Expanders and alerts */
[data-testid="stExpander"]{background:#FFFFFF;border:1px solid var(--border)!important;border-radius:10px!important;}
[data-testid="stExpander"] summary p{color:var(--navy)!important;font-weight:700!important;}
[data-testid="stAlert"] p{color:var(--text)!important;}

@media(max-width:900px){
  .block-container{padding:0 18px 48px;}.app-topbar{padding-left:20px;padding-right:20px;}
  .stat-strip{grid-template-columns:repeat(2,1fr);}.top-right{justify-content:flex-start;}.week-label{min-width:150px;}
}
@media(max-width:560px){
  .brand h1{font-size:18px!important;}.brand-sub{font-size:11.5px;}.mode-tab{padding:9px 12px;font-size:12px;}
  .stat-strip{grid-template-columns:1fr 1fr;}.stat-card{padding:13px;}.stat-card .n{font-size:24px;}
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
