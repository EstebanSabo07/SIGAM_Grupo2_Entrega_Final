"""Reporting exports for SIGAM snapshots and audiences."""

from __future__ import annotations

import io
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import pandas as pd

from data.presentation_service import get_municipality_snapshot_view, get_national_snapshot_view
from data.snapshot import AUDIENCE_ADMIN, AUDIENCE_MUNICIPAL, AUDIENCE_PUBLIC, SnapshotContext
from data.text_utils import normalized_contains


LEVEL_ORDER = ["Inicial", "Básico", "Intermedio", "Avanzado", "Optimizando"]
LEVEL_INDEX = {level: index for index, level in enumerate(LEVEL_ORDER, start=1)}


def _reportlab_import_error() -> str | None:
    """Return the reportlab import error for the active runtime, when any.

    Returns:
        Import error text when ``reportlab`` is unavailable, otherwise ``None``.
    """

    try:
        import reportlab  # noqa: F401
    except ImportError as exc:
        return str(exc)
    return None


def pdf_export_available() -> bool:
    """Return whether the formal PDF backend is available.

    Returns:
        ``True`` when ``reportlab`` can be imported in the active runtime.
    """

    return _reportlab_import_error() is None


def pdf_export_status() -> dict[str, Any]:
    """Return diagnostic details for the formal PDF backend.

    Returns:
        Availability, runtime paths, import error, and a recommended install
        command for the Streamlit environment currently in use.
    """

    runtime_executable = sys.executable or "Python desconocido"
    streamlit_executable = shutil.which("streamlit")
    import_error = _reportlab_import_error()

    recommended_install_command = None
    if streamlit_executable:
        pip_executable = Path(streamlit_executable).with_name("pip.exe")
        if pip_executable.exists():
            recommended_install_command = f'"{pip_executable}" install reportlab'

    if recommended_install_command is None and runtime_executable != "Python desconocido":
        runtime_path = Path(runtime_executable)
        pip_executable = runtime_path.with_name("pip.exe")
        if pip_executable.exists():
            recommended_install_command = f'"{pip_executable}" install reportlab'
        else:
            recommended_install_command = f'"{runtime_executable}" -m pip install reportlab'

    return {
        "available": import_error is None,
        "runtime_executable": runtime_executable,
        "streamlit_executable": streamlit_executable,
        "import_error": import_error,
        "recommended_install_command": recommended_install_command,
    }


def active_runtime_executable() -> str:
    """Return the active Python executable path for the current Streamlit runtime.

    Returns:
        Absolute executable path when available, otherwise a fallback label.
    """

    return pdf_export_status()["runtime_executable"]


def export_csv(snapshot: SnapshotContext, audience: str, scope: dict[str, Any] | None = None) -> bytes:
    """Export a snapshot dataset as CSV.

    Args:
        snapshot: Snapshot context.
        audience: Consumer audience.
        scope: Optional export scope, such as a municipality code.

    Returns:
        CSV bytes.
    """

    scope = scope or {}
    municipality_code = scope.get("municipality_code")
    if municipality_code:
        view = get_municipality_snapshot_view(municipality_code, snapshot, audience)
        if audience == AUDIENCE_ADMIN:
            rows = []
            for service in view["services"]:
                for stage in service["stages"]:
                    rows.append(
                        {
                            "periodo": snapshot.label,
                            "municipalidad": view["municipality"]["nombre"],
                            "servicio": service["service_name"],
                            "etapa": stage["stage_name"],
                            "puntaje": round(stage["score"], 4),
                            "nivel": stage["level"],
                            "estado_operativo": service["operational_status"],
                        }
                    )
            return pd.DataFrame(rows).to_csv(index=False).encode("utf-8-sig")

        rows = []
        for service in view["services"]:
            for stage in service["stages"]:
                row = {
                    "periodo": snapshot.label,
                    "municipalidad": view["municipality"]["nombre"],
                    "provincia": view["municipality"].get("provincia"),
                    "region": view["municipality"].get("region"),
                    "eje": service["axis_name"],
                    "servicio": service["service_name"],
                    "etapa": stage["stage_name"],
                    "nivel": stage["level"],
                }
                if audience == AUDIENCE_MUNICIPAL:
                    row.update(
                        {
                            "estado_operativo": service["operational_status"],
                            "fecha_actualizacion": service["update_date"],
                            "antiguedad_meses": service["data_age_months"],
                            "progreso_servicio_pct": service["service_progress_pct"],
                        }
                    )
                rows.append(row)
        return pd.DataFrame(rows).to_csv(index=False).encode("utf-8-sig")

    national = get_national_snapshot_view(snapshot, audience)
    if audience == AUDIENCE_ADMIN:
        rows = [
            {
                "periodo": snapshot.label,
                "codigo": municipality["municipality"]["codigo"],
                "municipalidad": municipality["municipality"]["nombre"],
                "provincia": municipality["municipality"].get("provincia"),
                "region": municipality["municipality"].get("region"),
                "puntaje": municipality["puntaje_pct"],
                "nivel": municipality["level"],
                "posicion": municipality["position"],
            }
            for municipality in national["municipalities"]
        ]
        return pd.DataFrame(rows).to_csv(index=False).encode("utf-8-sig")

    rows = [
        {
            "periodo": snapshot.label,
            "codigo": municipality["codigo"],
            "municipalidad": municipality["municipalidad"],
            "provincia": municipality["provincia"],
            "region": municipality["region"],
            "nivel": municipality["nivel"],
        }
        for municipality in national["municipalities"]
    ]
    return pd.DataFrame(rows).to_csv(index=False).encode("utf-8-sig")


def export_pdf(
    snapshot: SnapshotContext,
    audience: str,
    scope: dict[str, Any] | None = None,
    filters: dict[str, Any] | None = None,
) -> bytes:
    """Export a lightweight PDF summary for a snapshot scope.

    Args:
        snapshot: Snapshot context.
        audience: Consumer audience.
        scope: Optional export scope.
        filters: Optional serialized filters used by the current UI view.

    Returns:
        PDF bytes.
    """

    scope = scope or {}
    filters = filters or {}
    status = pdf_export_status()
    if audience in {AUDIENCE_PUBLIC, AUDIENCE_MUNICIPAL} and not status["available"]:
        raise RuntimeError(
            "El backend de PDF formal no está disponible en este entorno. "
            "Instale reportlab en el intérprete que ejecuta Streamlit."
        )
    municipality_code = scope.get("municipality_code")
    if municipality_code:
        view = get_municipality_snapshot_view(municipality_code, snapshot, audience)
        if audience == AUDIENCE_MUNICIPAL:
            return _municipal_pdf_bytes(snapshot, view)
        lines = [
            f"Periodo: {snapshot.label}",
            f"Municipalidad: {view['municipality']['nombre']}",
            f"Nivel de madurez: {view['level']}",
        ]
        if audience == AUDIENCE_ADMIN:
            lines.append(f"Puntaje: {view['puntaje_pct']}%")
        else:
            lines.append("Resumen por servicio:")
            for service in view["services"][:8]:
                if audience == AUDIENCE_MUNICIPAL:
                    lines.append(
                        f"- {service['service_name']}: {service['level']} | {service['operational_status']}"
                    )
                else:
                    lines.append(f"- {service['service_name']}: {service['level']}")
        return _simple_pdf_bytes("SIGAM Municipal", lines)

    view = get_national_snapshot_view(snapshot, audience)
    if audience == AUDIENCE_PUBLIC:
        report = _build_public_report_payload(snapshot, filters)
        return _public_pdf_bytes(snapshot, report, filters)

    lines = [
        f"Periodo: {snapshot.label}",
        f"Municipalidades consideradas: {view['total_municipalities']}",
    ]
    for level, count in sorted(view["distribution_by_level"].items()):
        lines.append(f"- {level}: {count}")
    if audience == AUDIENCE_ADMIN:
        lines.append(f"Promedio nacional: {round(view['average_score'] * 100, 2)}%")
    return _simple_pdf_bytes("SIGAM Nacional", lines)


def _municipal_pdf_bytes(snapshot: SnapshotContext, view: dict[str, Any]) -> bytes:
    """Generate the municipal PDF report.

    Args:
        snapshot: Snapshot context.
        view: Municipal view model.

    Returns:
        PDF bytes.
    """

    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.65 * inch,
        rightMargin=0.65 * inch,
        topMargin=0.9 * inch,
        bottomMargin=0.65 * inch,
        pageCompression=0,
    )
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="SigamBodyMunicipal",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13,
            textColor=colors.HexColor("#334155"),
            alignment=TA_LEFT,
        )
    )
    story = [
        Paragraph("Reporte municipal SIGAM", styles["Title"]),
        Spacer(1, 8),
        Paragraph(
            (
                "Resumen del estado de actualización y completitud por servicio para la municipalidad "
                "seleccionada en el período consultado."
            ),
            styles["SigamBodyMunicipal"],
        ),
        Spacer(1, 10),
        Paragraph(f"<b>Período:</b> {snapshot.label}", styles["SigamBodyMunicipal"]),
        Paragraph(f"<b>Municipalidad:</b> {view['municipality']['nombre']}", styles["SigamBodyMunicipal"]),
        Paragraph(f"<b>Nivel vigente:</b> {view['level']}", styles["SigamBodyMunicipal"]),
        Paragraph(
            (
                f"<b>Completitud global:</b> {view['completion_pct']:.1f}% · "
                f"<b>Servicios urgentes:</b> {view['services_urgent']} · "
                f"<b>Servicios al día:</b> {view['services_up_to_date']}"
            ),
            styles["SigamBodyMunicipal"],
        ),
        Spacer(1, 10),
    ]
    service_rows = [["Servicio", "Estado", "Completitud", "Antigüedad", "Última actualización"]]
    for service in view["priority_services"]:
        service_rows.append(
            [
                service["service_name"],
                service["freshness_status"],
                f"{service['service_progress_pct']:.0f}%",
                f"{service['data_age_months'] if service['data_age_months'] is not None else '—'} mes(es)",
                service["update_date"] or "Sin registros",
            ]
        )
    services_table = Table(service_rows, repeatRows=1, colWidths=[170, 90, 70, 85, 110])
    services_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1A3A6B")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.3),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D8E4F2")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    story.append(services_table)

    def draw_header(canvas, document) -> None:
        """Draw a consistent municipal SIGAM header on each page."""

        canvas.saveState()
        canvas.setFillColor(colors.HexColor("#1A3A6B"))
        canvas.rect(0, letter[1] - 44, letter[0], 44, fill=1, stroke=0)
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 12)
        canvas.drawString(46, letter[1] - 28, "SIGAM · Portal municipal")
        canvas.setFont("Helvetica", 9)
        canvas.drawRightString(letter[0] - 46, letter[1] - 28, f"Corte {snapshot.label}")
        canvas.restoreState()

    doc.build(story, onFirstPage=draw_header, onLaterPages=draw_header)
    return buffer.getvalue()


def _build_public_report_payload(snapshot: SnapshotContext, filters: dict[str, Any]) -> dict[str, Any]:
    """Build a filtered public-report payload from the public snapshot view.

    Args:
        snapshot: Snapshot context.
        filters: Serialized public-view filters.

    Returns:
        Filtered rows and aggregated values for PDF rendering.
    """

    national = get_national_snapshot_view(snapshot, AUDIENCE_PUBLIC)
    municipalities_df = pd.DataFrame(national["municipalities"])
    filtered_df = municipalities_df.copy()
    search = str(filters.get("search") or "").strip()
    region = filters.get("region") or "Todas"
    province = filters.get("province") or "Todas"
    level = filters.get("level") or "Todos"

    if search:
        filtered_df = filtered_df[
            filtered_df.apply(
                lambda row: normalized_contains(
                    " ".join(
                        str(row[column] or "")
                        for column in ["municipalidad", "provincia", "region"]
                        if column in row
                    ),
                    search,
                ),
                axis=1,
            )
        ]
    if region != "Todas":
        filtered_df = filtered_df[filtered_df["region"] == region]
    if province != "Todas":
        filtered_df = filtered_df[filtered_df["provincia"] == province]
    if level != "Todos":
        filtered_df = filtered_df[filtered_df["nivel"] == level]

    visible_codes = set(filtered_df["codigo"].tolist())
    filtered_candidates = [
        item for item in national["comparison_candidates"] if item["codigo"] in visible_codes
    ]

    distribution = Counter(filtered_df["nivel"].tolist())
    if not distribution:
        distribution = Counter(national["distribution_by_level"])

    service_level_counts: dict[str, Counter] = defaultdict(Counter)
    for municipality in filtered_candidates:
        for service_name, service_level in municipality["service_levels"].items():
            service_level_counts[service_name][service_level] += 1

    if not service_level_counts:
        for service in national["service_summaries"]:
            service_level_counts[service["service_name"]].update(service["level_distribution"])

    service_summaries = []
    for service_name, counts in sorted(service_level_counts.items()):
        total = sum(counts.values())
        maturity_index = 0.0
        if total > 0:
            maturity_index = round(
                sum(LEVEL_INDEX.get(level, 0) * count for level, count in counts.items()) / total,
                2,
            )
        predominant_level = max(counts, key=counts.get) if counts else "Inicial"
        service_summaries.append(
            {
                "service_name": service_name,
                "predominant_level": predominant_level,
                "maturity_index": maturity_index,
            }
        )

    return {
        "distribution": dict(distribution),
        "service_summaries": service_summaries,
        "municipalities": filtered_df.rename(
            columns={
                "municipalidad": "Municipalidad",
                "provincia": "Provincia",
                "region": "Región",
                "nivel": "Nivel",
            }
        )[["Municipalidad", "Provincia", "Región", "Nivel"]],
        "total_rows": len(filtered_df),
    }


def _public_pdf_bytes(
    snapshot: SnapshotContext,
    report: dict[str, Any],
    filters: dict[str, Any],
) -> bytes:
    """Generate the public PDF report.

    Args:
        snapshot: Snapshot context.
        report: Filtered public-report payload.
        filters: Active UI filters.

    Returns:
        PDF bytes.
    """

    from reportlab.graphics.charts.barcharts import HorizontalBarChart
    from reportlab.graphics.charts.piecharts import Pie
    from reportlab.graphics.shapes import Drawing, Rect, String
    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    level_colors = {
        "Inicial": colors.HexColor("#DC3545"),
        "Básico": colors.HexColor("#FD7E14"),
        "Intermedio": colors.HexColor("#2196F3"),
        "Avanzado": colors.HexColor("#20C997"),
        "Optimizando": colors.HexColor("#7B2FBE"),
    }
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.65 * inch,
        rightMargin=0.65 * inch,
        topMargin=1.0 * inch,
        bottomMargin=0.65 * inch,
        pageCompression=0,
    )
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="SigamBody",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13,
            textColor=colors.HexColor("#334155"),
            alignment=TA_LEFT,
        )
    )
    styles.add(
        ParagraphStyle(
            name="SigamSection",
            parent=styles["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=15,
            textColor=colors.HexColor("#1A3A6B"),
            spaceAfter=6,
            spaceBefore=4,
        )
    )

    story = [
        Paragraph("Dashboard Público de Gestión Municipal", styles["Title"]),
        Spacer(1, 8),
        Paragraph(
            (
                "Reporte resumido generado desde la vista pública de SIGAM. "
                "Presenta el período seleccionado, los filtros activos, la distribución "
                "de niveles de madurez, la madurez ordinal por servicio y la tabla visible "
                "de municipalidades."
            ),
            styles["SigamBody"],
        ),
        Spacer(1, 10),
        Paragraph(f"<b>Período seleccionado:</b> {snapshot.label}", styles["SigamBody"]),
        Paragraph("<b>Filtros aplicados:</b>", styles["SigamBody"]),
    ]
    for line in _filters_as_lines(filters):
        story.append(Paragraph(line, styles["SigamBody"]))
    story.extend(
        [
            Spacer(1, 10),
            Paragraph("Resumen nacional filtrado", styles["SigamSection"]),
            Paragraph(
                (
                    "La gráfica circular resume la cantidad de municipalidades visibles "
                    "por nivel de madurez bajo los filtros activos."
                ),
                styles["SigamBody"],
            ),
            Spacer(1, 6),
            _build_distribution_drawing(
                report["distribution"],
                level_colors,
                Pie,
                Drawing,
                Rect,
                String,
            ),
            Spacer(1, 12),
            Paragraph("Madurez por servicio", styles["SigamSection"]),
            Paragraph(
                (
                    "El siguiente gráfico ordena los servicios desde menor hasta mayor "
                    "madurez ordinal, usando únicamente niveles categóricos públicos."
                ),
                styles["SigamBody"],
            ),
            Spacer(1, 6),
            _build_service_chart_drawing(
                report["service_summaries"],
                level_colors,
                HorizontalBarChart,
                Drawing,
                String,
                colors,
            ),
            PageBreak(),
            Paragraph("Municipalidades visibles", styles["SigamSection"]),
            Paragraph(
                (
                    f"La tabla siguiente contiene {report['total_rows']} municipalidad(es) "
                    "coincidente(s) con la búsqueda y filtros activos."
                ),
                styles["SigamBody"],
            ),
            Spacer(1, 8),
            _build_public_table(report["municipalities"], Table, TableStyle, colors),
        ]
    )

    def draw_header(canvas, document) -> None:
        """Draw a consistent SIGAM header on each PDF page."""

        canvas.saveState()
        canvas.setFillColor(colors.HexColor("#1A3A6B"))
        canvas.rect(0, letter[1] - 44, letter[0], 44, fill=1, stroke=0)
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 12)
        canvas.drawString(46, letter[1] - 28, "SIGAM · Consulta pública")
        canvas.setFont("Helvetica", 9)
        canvas.drawRightString(letter[0] - 46, letter[1] - 28, f"Corte {snapshot.label}")
        canvas.restoreState()

    doc.build(story, onFirstPage=draw_header, onLaterPages=draw_header)
    return buffer.getvalue()


def _filters_as_lines(filters: dict[str, Any]) -> list[str]:
    """Serialize active filters into human-readable lines.

    Args:
        filters: UI filters.

    Returns:
        Filter lines for textual or PDF export.
    """

    return [
        f"- Búsqueda: {filters.get('search') or 'Sin filtro'}",
        f"- Región: {filters.get('region') or 'Todas'}",
        f"- Provincia: {filters.get('province') or 'Todas'}",
        f"- Nivel: {filters.get('level') or 'Todos'}",
    ]


def _build_distribution_drawing(
    distribution: dict[str, int],
    level_colors: dict[str, Any],
    pie_class: Any,
    drawing_class: Any,
    rect_class: Any,
    string_class: Any,
) -> Any:
    """Create the public distribution chart drawing for the PDF report.

    Args:
        distribution: Level distribution counts.
        level_colors: ReportLab colors keyed by level.
        pie_class: ReportLab pie chart class.
        drawing_class: ReportLab drawing class.
        rect_class: ReportLab rectangle shape class.
        string_class: ReportLab string class.

    Returns:
        ReportLab drawing instance.
    """

    drawing = drawing_class(480, 230)
    pie = pie_class()
    pie.x = 32
    pie.y = 24
    pie.width = 180
    pie.height = 180
    labels = [level for level in LEVEL_ORDER if distribution.get(level, 0) > 0]
    values = [distribution.get(level, 0) for level in labels]
    pie.data = values or [1]
    pie.labels = labels or ["Sin datos"]
    pie.slices.strokeWidth = 0.5
    for index, level in enumerate(labels):
        pie.slices[index].fillColor = level_colors[level]
    drawing.add(pie)
    drawing.add(string_class(260, 190, "Distribución por nivel", fontName="Helvetica-Bold", fontSize=11))
    y = 168
    for level in labels:
        drawing.add(
            rect_class(
                260,
                y - 8,
                10,
                10,
                fillColor=level_colors[level],
                strokeColor=level_colors[level],
            )
        )
        drawing.add(
            string_class(
                276,
                y - 6,
                f"{level}: {distribution[level]}",
                fontName="Helvetica",
                fontSize=9,
            )
        )
        y -= 20
    return drawing


def _build_service_chart_drawing(
    services: list[dict[str, Any]],
    level_colors: dict[str, Any],
    bar_chart_class: Any,
    drawing_class: Any,
    string_class: Any,
    colors: Any,
) -> Any:
    """Create the public service-maturity chart drawing for the PDF report.

    Args:
        services: Public service summaries with ordinal maturity values.
        level_colors: ReportLab colors keyed by level.
        bar_chart_class: ReportLab horizontal bar chart class.
        drawing_class: ReportLab drawing class.
        string_class: ReportLab string class.
        colors: ReportLab colors module.

    Returns:
        ReportLab drawing instance.
    """

    sorted_services = sorted(services, key=lambda item: item["maturity_index"])
    top_services = sorted_services[:10]
    drawing = drawing_class(480, 280)
    chart = bar_chart_class()
    chart.x = 140
    chart.y = 28
    chart.width = 300
    chart.height = 210
    chart.data = [[service["maturity_index"] for service in top_services]]
    chart.valueAxis.valueMin = 0
    chart.valueAxis.valueMax = 5
    chart.valueAxis.valueSteps = [1, 2, 3, 4, 5]
    chart.categoryAxis.labels.boxAnchor = "e"
    chart.categoryAxis.labels.dx = -8
    chart.categoryAxis.categoryNames = [service["service_name"][:34] for service in top_services]
    chart.bars[0].fillColor = colors.HexColor("#1A3A6B")
    chart.bars[0].strokeColor = colors.HexColor("#1A3A6B")
    chart.barSpacing = 4
    chart.groupSpacing = 8
    drawing.add(chart)
    drawing.add(string_class(140, 248, "Madurez ordinal por servicio", fontName="Helvetica-Bold", fontSize=11))
    y = 228
    for service in top_services:
        drawing.add(
            string_class(
                24,
                y,
                service["predominant_level"],
                fontName="Helvetica",
                fontSize=7,
                fillColor=level_colors.get(service["predominant_level"]),
            )
        )
        y -= 20
    return drawing


def _build_public_table(dataframe: pd.DataFrame, table_class: Any, table_style_class: Any, colors: Any) -> Any:
    """Create the always-visible public municipality table for the PDF report.

    Args:
        dataframe: Visible municipality table.
        table_class: ReportLab table class.
        table_style_class: ReportLab table style class.
        colors: ReportLab colors module.

    Returns:
        Styled ReportLab table instance.
    """

    rows = [dataframe.columns.tolist()]
    rows.extend(dataframe.head(28).fillna("—").values.tolist())
    table = table_class(rows, repeatRows=1, colWidths=[160, 115, 105, 90])
    table.setStyle(
        table_style_class(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1A3A6B")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8.5),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
                ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D8E4F2")),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 6),
                ("RIGHTPADDING", (0, 0), (-1, -1), 6),
                ("TOPPADDING", (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return table


def _simple_pdf_bytes(title: str, lines: list[str]) -> bytes:
    """Generate a minimal single-page PDF document.

    Args:
        title: PDF title.
        lines: Body lines to print.

    Returns:
        PDF bytes.
    """

    escaped_lines = [title, ""] + lines
    text_lines = [f"({line.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)')}) Tj" for line in escaped_lines]
    commands = ["BT", "/F1 18 Tf", "50 780 Td"] + text_lines[:1]
    for line in text_lines[1:]:
        commands.extend(["T*", line])
    commands.append("ET")
    stream = "\n".join(commands).encode("latin-1", errors="replace")
    objects = []
    objects.append(b"1 0 obj << /Type /Catalog /Pages 2 0 R >> endobj\n")
    objects.append(b"2 0 obj << /Type /Pages /Kids [3 0 R] /Count 1 >> endobj\n")
    objects.append(
        b"3 0 obj << /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
        b"/Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >> endobj\n"
    )
    objects.append(b"4 0 obj << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> endobj\n")
    objects.append(
        f"5 0 obj << /Length {len(stream)} >> stream\n".encode("latin-1")
        + stream
        + b"\nendstream endobj\n"
    )

    output = io.BytesIO()
    output.write(b"%PDF-1.4\n")
    offsets = [0]
    for obj in objects:
        offsets.append(output.tell())
        output.write(obj)
    xref_position = output.tell()
    output.write(f"xref\n0 {len(objects) + 1}\n".encode("latin-1"))
    output.write(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        output.write(f"{offset:010d} 00000 n \n".encode("latin-1"))
    output.write(
        f"trailer << /Size {len(objects) + 1} /Root 1 0 R >>\nstartxref\n{xref_position}\n%%EOF".encode("latin-1")
    )
    return output.getvalue()
