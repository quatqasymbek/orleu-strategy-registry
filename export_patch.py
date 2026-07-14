from __future__ import annotations

import csv
import io
import re
from collections import defaultdict
from datetime import datetime
from functools import lru_cache
from typing import Any

import streamlit as st
import xlsxwriter

from reference_data import DEPARTMENT_BY_ID, DEPARTMENTS, STATUS_LABELS, STATUS_ORDER

NAVY = "#002147"
BLUE = "#25588A"
YELLOW = "#FFCA02"
PALE_BLUE = "#EAF1F8"
PALE_YELLOW = "#FFF5CC"
BORDER = "#D5DEE8"
TEXT = "#1F2937"
MUTED = "#667085"
WHITE = "#FFFFFF"
RED = "#B42318"
GREEN = "#147D64"
AMBER = "#B76E00"
FONT = "Roboto"

_INSTALLED = False
_ORIGINAL_EXPANDER = None
_ORIGINAL_DOWNLOAD_BUTTON = None


def _parse_date(value: str | None) -> datetime | None:
    text = (value or "").strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M:%S.%f", "%d.%m.%Y"):
        try:
            return datetime.strptime(text[:26], fmt)
        except ValueError:
            pass
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


def _week_from_filename(file_name: str | None, rows: list[dict[str, str]]) -> str:
    if rows and rows[0].get("week_id"):
        return rows[0]["week_id"]
    match = re.search(r"(\d{4}-W\d{2})", file_name or "")
    return match.group(1) if match else "week"


def _formats(workbook: xlsxwriter.Workbook) -> dict[str, Any]:
    base = {"font_name": FONT, "font_size": 10, "font_color": TEXT}
    return {
        "title": workbook.add_format(
            {
                "font_name": FONT,
                "font_size": 18,
                "bold": True,
                "font_color": WHITE,
                "bg_color": NAVY,
                "align": "left",
                "valign": "vcenter",
            }
        ),
        "subtitle": workbook.add_format(
            {
                "font_name": FONT,
                "font_size": 10,
                "font_color": "#D9E5F2",
                "bg_color": NAVY,
                "align": "left",
                "valign": "vcenter",
            }
        ),
        "section": workbook.add_format(
            {
                "font_name": FONT,
                "font_size": 12,
                "bold": True,
                "font_color": NAVY,
                "bottom": 2,
                "bottom_color": YELLOW,
            }
        ),
        "header": workbook.add_format(
            {
                "font_name": FONT,
                "font_size": 10,
                "bold": True,
                "font_color": WHITE,
                "bg_color": BLUE,
                "border": 1,
                "border_color": WHITE,
                "align": "center",
                "valign": "vcenter",
                "text_wrap": True,
            }
        ),
        "cell": workbook.add_format(
            {
                **base,
                "border": 1,
                "border_color": BORDER,
                "valign": "top",
                "text_wrap": True,
            }
        ),
        "center": workbook.add_format(
            {
                **base,
                "border": 1,
                "border_color": BORDER,
                "align": "center",
                "valign": "vcenter",
                "text_wrap": True,
            }
        ),
        "date": workbook.add_format(
            {
                **base,
                "border": 1,
                "border_color": BORDER,
                "align": "center",
                "valign": "vcenter",
                "num_format": "dd.mm.yyyy",
            }
        ),
        "datetime": workbook.add_format(
            {
                **base,
                "border": 1,
                "border_color": BORDER,
                "align": "center",
                "valign": "vcenter",
                "num_format": "dd.mm.yyyy hh:mm",
            }
        ),
        "kpi_value": workbook.add_format(
            {
                "font_name": FONT,
                "font_size": 22,
                "bold": True,
                "font_color": NAVY,
                "bg_color": WHITE,
                "border": 1,
                "border_color": BORDER,
                "align": "center",
                "valign": "vcenter",
            }
        ),
        "kpi_label": workbook.add_format(
            {
                "font_name": FONT,
                "font_size": 9,
                "bold": True,
                "font_color": MUTED,
                "bg_color": WHITE,
                "border": 1,
                "border_color": BORDER,
                "align": "center",
                "valign": "vcenter",
                "text_wrap": True,
            }
        ),
        "note": workbook.add_format(
            {"font_name": FONT, "font_size": 9, "font_color": MUTED, "italic": True, "text_wrap": True}
        ),
        "status_done": workbook.add_format(
            {**base, "bold": True, "font_color": GREEN, "bg_color": "#E9F7F2", "border": 1, "border_color": BORDER, "align": "center"}
        ),
        "status_risk": workbook.add_format(
            {**base, "bold": True, "font_color": AMBER, "bg_color": PALE_YELLOW, "border": 1, "border_color": BORDER, "align": "center"}
        ),
        "status_overdue": workbook.add_format(
            {**base, "bold": True, "font_color": RED, "bg_color": "#FDECE9", "border": 1, "border_color": BORDER, "align": "center"}
        ),
        "status_default": workbook.add_format(
            {**base, "font_color": BLUE, "bg_color": PALE_BLUE, "border": 1, "border_color": BORDER, "align": "center"}
        ),
        "report_yes": workbook.add_format(
            {**base, "bold": True, "font_color": GREEN, "bg_color": "#E9F7F2", "border": 1, "border_color": BORDER, "align": "center"}
        ),
        "report_no": workbook.add_format(
            {**base, "bold": True, "font_color": RED, "bg_color": "#FDECE9", "border": 1, "border_color": BORDER, "align": "center"}
        ),
    }


def _status_key(label: str) -> str:
    label = (label or "").strip()
    for key, value in STATUS_LABELS.items():
        if value == label:
            return key
    return label


def _status_format(formats: dict[str, Any], status_key: str):
    if status_key == "done":
        return formats["status_done"]
    if status_key == "risk":
        return formats["status_risk"]
    if status_key == "overdue":
        return formats["status_overdue"]
    return formats["status_default"]


def _write_title(sheet, formats: dict[str, Any], week_id: str, last_col: int) -> None:
    sheet.merge_range(0, 0, 1, last_col, "Реестр еженедельного исполнения", formats["title"])
    sheet.merge_range(
        2,
        0,
        2,
        last_col,
        f"{week_id} · сформировано {datetime.now():%d.%m.%Y %H:%M}",
        formats["subtitle"],
    )
    sheet.set_row(0, 26)
    sheet.set_row(1, 14)
    sheet.set_row(2, 20)


def _enrich_rows(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for index, row in enumerate(rows, start=1):
        department_id = (row.get("department_id") or "").strip()
        dept = DEPARTMENT_BY_ID.get(department_id, {})
        status_label = (row.get("status") or "").strip()
        result.append(
            {
                "number": index,
                "week_id": row.get("week_id") or "",
                "department_id": department_id,
                "department": dept.get("name", department_id),
                "block": dept.get("block", ""),
                "direction": row.get("direction") or "",
                "task": row.get("task") or "",
                "activity": row.get("activity") or "",
                "result": row.get("result") or "",
                "deadline": _parse_date(row.get("deadline")),
                "status_label": status_label,
                "status_key": _status_key(status_label),
                "is_major": (row.get("is_major") or "").strip().lower() in {"да", "true", "1", "yes"},
                "meeting_date": _parse_date(row.get("meeting_date")),
                "comment": row.get("comment") or "",
                "updated_at": _parse_date(row.get("updated_at")),
            }
        )
    return result


def _write_tasks_sheet(
    workbook: xlsxwriter.Workbook,
    sheet_name: str,
    table_name: str,
    week_id: str,
    rows: list[dict[str, Any]],
    formats: dict[str, Any],
) -> None:
    headers = [
        "№",
        "Код подразделения",
        "Подразделение",
        "Организационный блок",
        "Стратегическое направление",
        "Задача",
        "Мероприятие",
        "Ожидаемый / фактический результат",
        "Срок",
        "Статус",
        "Крупный проект",
        "Дата доклада",
        "Комментарий / риски",
        "Обновлено",
    ]
    sheet = workbook.add_worksheet(sheet_name)
    _write_title(sheet, formats, week_id, len(headers) - 1)
    header_row = 4
    sheet.write_row(header_row, 0, headers, formats["header"])

    for offset, row in enumerate(rows, start=1):
        excel_row = header_row + offset
        values = [
            row["number"],
            row["department_id"],
            row["department"],
            row["block"],
            row["direction"],
            row["task"],
            row["activity"],
            row["result"],
        ]
        for col, value in enumerate(values):
            sheet.write(excel_row, col, value, formats["center"] if col < 2 else formats["cell"])
        if row["deadline"]:
            sheet.write_datetime(excel_row, 8, row["deadline"], formats["date"])
        else:
            sheet.write(excel_row, 8, "", formats["center"])
        sheet.write(excel_row, 9, row["status_label"], _status_format(formats, row["status_key"]))
        sheet.write(excel_row, 10, "Да" if row["is_major"] else "Нет", formats["center"])
        if row["meeting_date"]:
            sheet.write_datetime(excel_row, 11, row["meeting_date"], formats["date"])
        else:
            sheet.write(excel_row, 11, "", formats["center"])
        sheet.write(excel_row, 12, row["comment"], formats["cell"])
        if row["updated_at"]:
            sheet.write_datetime(excel_row, 13, row["updated_at"], formats["datetime"])
        else:
            sheet.write(excel_row, 13, "", formats["center"])

    last_row = header_row + len(rows)
    if rows:
        sheet.add_table(
            header_row,
            0,
            last_row,
            len(headers) - 1,
            {
                "name": table_name,
                "style": "Table Style Medium 2",
                "columns": [{"header": header} for header in headers],
            },
        )
    else:
        sheet.autofilter(header_row, 0, header_row, len(headers) - 1)
        sheet.merge_range(header_row + 2, 0, header_row + 3, len(headers) - 1, "Нет данных для выбранной недели.", formats["note"])

    sheet.freeze_panes(header_row + 1, 0)
    sheet.set_column(0, 0, 5)
    sheet.set_column(1, 1, 15)
    sheet.set_column(2, 3, 34)
    sheet.set_column(4, 5, 38)
    sheet.set_column(6, 7, 42)
    sheet.set_column(8, 11, 16)
    sheet.set_column(12, 12, 34)
    sheet.set_column(13, 13, 20)
    sheet.set_landscape()
    sheet.fit_to_pages(1, 0)
    sheet.set_margins(0.3, 0.3, 0.5, 0.5)


@lru_cache(maxsize=16)
def _csv_to_xlsx(csv_bytes: bytes, file_name: str) -> bytes:
    csv_text = csv_bytes.decode("utf-8-sig")
    raw_rows = list(csv.DictReader(io.StringIO(csv_text)))
    week_id = _week_from_filename(file_name, raw_rows)
    rows = _enrich_rows(raw_rows)

    status_counts = {status: 0 for status in STATUS_ORDER}
    by_department: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        status_counts[row["status_key"]] = status_counts.get(row["status_key"], 0) + 1
        by_department[row["department_id"]].append(row)

    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output, {"in_memory": True})
    workbook.set_properties(
        {
            "title": f"Реестр еженедельного исполнения {week_id}",
            "subject": "Недельный свод исполнения Стратегии",
            "company": "АО «НЦПК «Өрлеу»",
            "comments": "Сформировано автоматически в Streamlit",
        }
    )
    formats = _formats(workbook)

    total = len(rows)
    done = status_counts.get("done", 0)
    in_progress = status_counts.get("in_progress", 0)
    risk = status_counts.get("risk", 0) + status_counts.get("overdue", 0)
    major = sum(row["is_major"] for row in rows)
    submitted = sum(bool(by_department.get(dept["id"])) for dept in DEPARTMENTS)

    summary = workbook.add_worksheet("Свод")
    _write_title(summary, formats, week_id, 10)
    summary.hide_gridlines(2)
    summary.set_column("A:A", 3)
    summary.set_column("B:K", 14)
    summary.set_column("L:L", 3)

    kpis = [
        ("Всего записей", total),
        ("Выполнено", done),
        ("В работе", in_progress),
        ("Риск / просрочка", risk),
        ("Крупные проекты", major),
    ]
    for index, (label, value) in enumerate(kpis):
        start_col = 1 + index * 2
        summary.merge_range(4, start_col, 5, start_col + 1, value, formats["kpi_value"])
        summary.merge_range(6, start_col, 6, start_col + 1, label, formats["kpi_label"])

    summary.write(9, 1, "Статус исполнения", formats["section"])
    summary.write_row(10, 1, ["Статус", "Количество"], formats["header"])
    for idx, status in enumerate(STATUS_ORDER, start=11):
        summary.write(idx, 1, STATUS_LABELS[status], formats["cell"])
        summary.write(idx, 2, status_counts.get(status, 0), formats["center"])

    chart = workbook.add_chart({"type": "column"})
    chart.add_series(
        {
            "name": "Количество",
            "categories": "=Свод!$B$12:$B$16",
            "values": "=Свод!$C$12:$C$16",
            "fill": {"color": BLUE},
            "border": {"color": BLUE},
            "data_labels": {"value": True},
        }
    )
    chart.set_title({"name": "Распределение по статусам"})
    chart.set_legend({"none": True})
    chart.set_y_axis({"major_gridlines": {"visible": False}, "min": 0})
    chart.set_chartarea({"border": {"none": True}})
    chart.set_plotarea({"border": {"none": True}})
    summary.insert_chart("E10", chart, {"x_scale": 1.1, "y_scale": 1.05})

    summary.write(18, 1, "Подача отчётности подразделениями", formats["section"])
    summary.write_row(19, 1, ["Показатель", "Значение"], formats["header"])
    summary.write(20, 1, "Всего подразделений", formats["cell"])
    summary.write(20, 2, len(DEPARTMENTS), formats["center"])
    summary.write(21, 1, "Есть записи", formats["cell"])
    summary.write(21, 2, submitted, formats["report_yes"])
    summary.write(22, 1, "Нет записей", formats["cell"])
    summary.write(22, 2, len(DEPARTMENTS) - submitted, formats["report_no"])
    summary.write(24, 1, "Примечание", formats["section"])
    summary.merge_range(
        25,
        1,
        27,
        10,
        "Статус «есть записи» означает, что подразделение внесло хотя бы одну запись за выбранную неделю. "
        "Отдельный workflow официальной подачи отчёта пока не реализован.",
        formats["note"],
    )

    reporting = workbook.add_worksheet("Подразделения")
    reporting_headers = [
        "№",
        "Код",
        "Подразделение",
        "Организационный блок",
        "Статус отчётности",
        "Всего записей",
        "Выполнено",
        "В работе",
        "Риск / просрочка",
        "Последнее обновление",
    ]
    _write_title(reporting, formats, week_id, len(reporting_headers) - 1)
    reporting.write_row(4, 0, reporting_headers, formats["header"])
    for index, dept in enumerate(DEPARTMENTS, start=1):
        dept_rows = by_department.get(dept["id"], [])
        excel_row = 4 + index
        last_updated = max((row["updated_at"] for row in dept_rows if row["updated_at"]), default=None)
        reporting.write(excel_row, 0, index, formats["center"])
        reporting.write(excel_row, 1, dept["id"], formats["center"])
        reporting.write(excel_row, 2, dept["name"], formats["cell"])
        reporting.write(excel_row, 3, dept["block"], formats["cell"])
        reporting.write(excel_row, 4, "Есть записи" if dept_rows else "Нет записей", formats["report_yes"] if dept_rows else formats["report_no"])
        reporting.write(excel_row, 5, len(dept_rows), formats["center"])
        reporting.write(excel_row, 6, sum(row["status_key"] == "done" for row in dept_rows), formats["center"])
        reporting.write(excel_row, 7, sum(row["status_key"] == "in_progress" for row in dept_rows), formats["center"])
        reporting.write(excel_row, 8, sum(row["status_key"] in {"risk", "overdue"} for row in dept_rows), formats["center"])
        if last_updated:
            reporting.write_datetime(excel_row, 9, last_updated, formats["datetime"])
        else:
            reporting.write(excel_row, 9, "", formats["center"])
    reporting.freeze_panes(5, 0)
    reporting.autofilter(4, 0, 4 + len(DEPARTMENTS), len(reporting_headers) - 1)
    reporting.set_column(0, 1, 10)
    reporting.set_column(2, 3, 36)
    reporting.set_column(4, 8, 18)
    reporting.set_column(9, 9, 20)

    _write_tasks_sheet(workbook, "Все задачи", "AllTasksTable", week_id, rows, formats)
    _write_tasks_sheet(
        workbook,
        "Риски и просрочка",
        "RisksTable",
        week_id,
        [row for row in rows if row["status_key"] in {"risk", "overdue"}],
        formats,
    )
    _write_tasks_sheet(
        workbook,
        "Крупные проекты",
        "MajorProjectsTable",
        week_id,
        [row for row in rows if row["is_major"]],
        formats,
    )

    workbook.close()
    output.seek(0)
    return output.getvalue()


def install_export_patch() -> None:
    global _INSTALLED, _ORIGINAL_EXPANDER, _ORIGINAL_DOWNLOAD_BUTTON
    if _INSTALLED:
        return

    _ORIGINAL_EXPANDER = st.expander
    _ORIGINAL_DOWNLOAD_BUTTON = st.download_button

    def patched_expander(label: str, *args, **kwargs):
        if label == "Администрирование и экспорт":
            container = st.container(border=True)
            container.markdown('<div class="panel-title">Администрирование и экспорт</div>', unsafe_allow_html=True)
            return container
        return _ORIGINAL_EXPANDER(label, *args, **kwargs)

    def patched_download_button(label: str, data=None, file_name=None, mime=None, *args, **kwargs):
        if label == "Скачать текущую неделю в CSV" and isinstance(data, (bytes, bytearray)):
            source = bytes(data)
            target_name = re.sub(r"\.csv$", ".xlsx", file_name or "orleu_weekly_report.xlsx", flags=re.IGNORECASE)
            if target_name == (file_name or ""):
                target_name = f"{target_name}.xlsx"
            return _ORIGINAL_DOWNLOAD_BUTTON(
                "Скачать недельный отчёт в Excel",
                data=_csv_to_xlsx(source, file_name or ""),
                file_name=target_name.replace("orleu-", "orleu_weekly_report_"),
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                *args,
                **kwargs,
            )
        return _ORIGINAL_DOWNLOAD_BUTTON(label, data=data, file_name=file_name, mime=mime, *args, **kwargs)

    st.expander = patched_expander
    st.download_button = patched_download_button
    _INSTALLED = True
