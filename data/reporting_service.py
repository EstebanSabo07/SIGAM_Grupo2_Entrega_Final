"""Reporting exports for SIGAM snapshots and audiences."""

from __future__ import annotations

import io
import shutil
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

import pandas as pd

from components.charts import distribucion_niveles_pie, madurez_servicios_horizontal
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


def _kaleido_import_error() -> str | None:
    """Return the kaleido import error for the active runtime, when any.

    Returns:
        Import error text when ``kaleido`` is unavailable, otherwise ``None``.
    """

    try:
        import kaleido  # noqa: F401
    except ImportError as exc:
        return str(exc)
    return None


def pdf_export_available() -> bool:
    """Return whether the formal PDF backend is available.

    Returns:
        ``True`` when ``reportlab`` can be imported in the active runtime.
    """

    return _reportlab_import_error() is None and _kaleido_import_error() is None


def pdf_export_status() -> dict[str, Any]:
    """Return diagnostic details for the formal PDF backend.

    Returns:
        Availability, runtime paths, import error, and a recommended install
        command for the Streamlit environment currently in use.
    """

    runtime_executable = sys.executable or "Python desconocido"
    streamlit_executable = shutil.which("streamlit")
    import_errors = {
        "reportlab": _reportlab_import_error(),
        "kaleido": _kaleido_import_error(),
    }
    missing_dependencies = [
        dependency
        for dependency, import_error in import_errors.items()
        if import_error is not None
    ]

    recommended_install_command = None
    if streamlit_executable:
        pip_executable = Path(streamlit_executable).with_name("pip.exe")
        if pip_executable.exists():
            recommended_install_command = f'"{pip_executable}" install reportlab kaleido'

    if recommended_install_command is None and runtime_executable != "Python desconocido":
        runtime_path = Path(runtime_executable)
        pip_executable = runtime_path.with_name("pip.exe")
        if pip_executable.exists():
            recommended_install_command = f'"{pip_executable}" install reportlab kaleido'
        else:
            recommended_install_command = f'"{runtime_executable}" -m pip install reportlab kaleido'

    return {
        "available": not missing_dependencies,
        "runtime_executable": runtime_executable,
        "streamlit_executable": streamlit_executable,
        "import_error": next((error for error in import_errors.values() if error), None),
        "import_errors": import_errors,
        "missing_dependencies": missing_dependencies,
        "recommended_install_command": recommended_install_command,
    }


def pdf_unavailable_message(status: dict[str, Any] | None = None) -> str:
    """Build a consistent warning message for missing PDF support.

    Args:
        status: Optional PDF backend status payload.

    Returns:
        Actionable message describing how to enable the formal PDF backend.
    """

    active_status = status or pdf_export_status()
    message = "El backend de PDF formal no está disponible en el entorno actual de Streamlit."
    if active_status.get("missing_dependencies"):
        dependencies = ", ".join(active_status["missing_dependencies"])
        message += f" Dependencias faltantes: {dependencies}."
    if active_status.get("recommended_install_command"):
        message += f" Instálelo con: `{active_status['recommended_install_command']}`."
    if active_status.get("runtime_executable"):
        message += f" Runtime activo: `{active_status['runtime_executable']}`."
    return message


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
    include_service_detail = bool(scope.get("include_service_detail"))
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
        if include_service_detail:
            rows = []
            for municipality in national["municipalities"]:
                for service in municipality["services"]:
                    rows.append(
                        {
                            "periodo": snapshot.label,
                            "codigo": municipality["municipality"]["codigo"],
                            "municipalidad": municipality["municipality"]["nombre"],
                            "provincia": municipality["municipality"].get("provincia"),
                            "region": municipality["municipality"].get("region"),
                            "eje": service.get("axis_name"),
                            "servicio": service["service_name"],
                            "puntaje": round(service["score"] * 100, 2),
                            "nivel": service["level"],
                            "estado_operativo": service.get("operational_status"),
                            "fecha_actualizacion": (
                                service["update_date"].isoformat()
                                if service.get("update_date")
                                else None
                            ),
                            "antiguedad_meses": service.get("data_age_months"),
                        }
                    )
            return pd.DataFrame(rows).to_csv(index=False).encode("utf-8-sig")

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
    """Export a formal PDF report for a snapshot scope.

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
    if not status["available"]:
        raise RuntimeError(pdf_unavailable_message(status))
    municipality_code = scope.get("municipality_code")
    if municipality_code:
        view = get_municipality_snapshot_view(municipality_code, snapshot, audience)
        if audience == AUDIENCE_MUNICIPAL:
            return _municipal_pdf_bytes(snapshot, view)
        if audience == AUDIENCE_ADMIN:
            return _admin_municipal_pdf_bytes(snapshot, view)

    view = get_national_snapshot_view(snapshot, audience)
    if audience == AUDIENCE_PUBLIC:
        report = _build_public_report_payload(snapshot, filters)
        return _public_pdf_bytes(snapshot, report, filters)

    return _admin_national_pdf_bytes(snapshot, view)


def _build_service_maturity_frame(services: list[dict[str, Any]]) -> pd.DataFrame:
    """Build a dataframe compatible with the shared service-maturity chart.

    Args:
        services: Service rows with at least ``service_name`` and ``level``.

    Returns:
        Dataframe sorted later by the chart builder.
    """

    rows = [
        {
            "service_name": service["service_name"],
            "predominant_level": service["level"],
            "maturity_index": LEVEL_INDEX.get(service["level"], 1),
            "maturity_label": service["level"],
        }
        for service in services
    ]
    return pd.DataFrame(rows)


def _plotly_figure_to_reportlab_image(
    figure: Any,
    width_inches: float,
    height_inches: float,
) -> Any:
    """Render a Plotly figure into a ReportLab image flowable.

    Args:
        figure: Plotly figure instance.
        width_inches: Target width in inches inside the PDF.
        height_inches: Target height in inches inside the PDF.

    Returns:
        ReportLab image flowable ready for ``story.append``.

    Raises:
        RuntimeError: If Plotly cannot render the figure into PNG bytes.
    """

    import plotly.io as pio
    from reportlab.lib.units import inch
    from reportlab.platypus import Image

    try:
        png_bytes = pio.to_image(
            figure,
            format="png",
            width=int(width_inches * 144),
            height=int(height_inches * 144),
            scale=2,
        )
    except Exception as exc:
        raise RuntimeError(
            "No se pudo renderizar el gráfico de Plotly para el PDF. "
            "Verifique la instalación de kaleido en el runtime activo."
        ) from exc

    return Image(io.BytesIO(png_bytes), width=width_inches * inch, height=height_inches * inch)


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
    maturity_df = _build_service_maturity_frame(view["services"])
    maturity_chart = _plotly_figure_to_reportlab_image(
        madurez_servicios_horizontal(
            maturity_df,
            height=max(360, len(maturity_df) * 30 + 120),
            prefer_inside_text=True,
            margin_left=190,
            margin_right=80,
        ),
        width_inches=6.85,
        height_inches=4.15,
    )
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
    story.extend(
        [
            Paragraph("Completitud y vigencia por servicio", styles["Heading2"]),
            Spacer(1, 6),
            services_table,
            Spacer(1, 14),
            Paragraph("Nivel de madurez por servicio", styles["Heading2"]),
            Spacer(1, 4),
            Paragraph(
                (
                    "La siguiente visual resume el nivel predominante observado en cada servicio "
                    "durante el período consultado."
                ),
                styles["SigamBodyMunicipal"],
            ),
            Spacer(1, 8),
            maturity_chart,
            Spacer(1, 12),
        ]
    )

    maturity_rows = [["Servicio", "Nivel de madurez", "Completitud", "Antigüedad"]]
    for service in sorted(
        view["services"],
        key=lambda item: (LEVEL_INDEX.get(item["level"], 1), item["service_name"]),
    ):
        maturity_rows.append(
            [
                service["service_name"],
                service["level"],
                f"{service['service_progress_pct']:.0f}%",
                f"{service['data_age_months'] if service['data_age_months'] is not None else '—'} mes(es)",
            ]
        )
    maturity_table = Table(maturity_rows, repeatRows=1, colWidths=[225, 120, 85, 95])
    maturity_table.setStyle(TableStyle(_pdf_table_style(colors, font_size=8.2)))
    story.extend(
        [
            Paragraph("Resumen de madurez por servicio", styles["Heading2"]),
            Spacer(1, 6),
            maturity_table,
        ]
    )

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


def _pdf_table_style(colors: Any, font_size: float = 8.3) -> Any:
    """Build the default ReportLab table style used across formal PDFs.

    Args:
        colors: ReportLab colors module.
        font_size: Table font size.

    Returns:
        List of ReportLab table-style commands.
    """

    return [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1A3A6B")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), font_size),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
        ("GRID", (0, 0), (-1, -1), 0.35, colors.HexColor("#D8E4F2")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]


def _admin_municipal_pdf_bytes(snapshot: SnapshotContext, view: dict[str, Any]) -> bytes:
    """Generate the formal admin municipal PDF report.

    Args:
        snapshot: Snapshot context.
        view: Administrator municipal view model.

    Returns:
        PDF bytes.
    """

    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    benchmark = view.get("benchmark_summary", {})
    position_national = benchmark.get("position_national")
    total_national = benchmark.get("total_national")
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
            name="SigamBodyAdminMunicipal",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13,
            textColor=colors.HexColor("#334155"),
            alignment=TA_LEFT,
        )
    )
    story = [
        Paragraph("Reporte municipal interno SIGAM", styles["Title"]),
        Spacer(1, 8),
        Paragraph(
            (
                "Resumen técnico de puntajes, vigencia y avance por servicio para la "
                "municipalidad seleccionada desde el portal interno de Contraloría."
            ),
            styles["SigamBodyAdminMunicipal"],
        ),
        Spacer(1, 10),
        Paragraph(f"<b>Período:</b> {snapshot.label}", styles["SigamBodyAdminMunicipal"]),
        Paragraph(f"<b>Municipalidad:</b> {view['municipality']['nombre']}", styles["SigamBodyAdminMunicipal"]),
        Paragraph(f"<b>Nivel vigente:</b> {view['level']}", styles["SigamBodyAdminMunicipal"]),
        Paragraph(
            f"<b>Puntaje total:</b> {view['puntaje_pct']:.2f}%",
            styles["SigamBodyAdminMunicipal"],
        ),
        Paragraph(
            (
                "<b>Posición nacional:</b> "
                f"{f'{position_national}/{total_national}' if position_national else 'Sin dato'}"
            ),
            styles["SigamBodyAdminMunicipal"],
        ),
        Spacer(1, 10),
    ]

    service_rows = [["Servicio", "Nivel", "Puntaje", "Estado", "Antigüedad", "Actualización"]]
    for service in view["services"]:
        update_date = service["update_date"].isoformat() if service.get("update_date") else "Sin registros"
        service_rows.append(
            [
                service["service_name"],
                service["level"],
                f"{service['score'] * 100:.2f}%",
                service["operational_status"],
                f"{service['data_age_months'] if service['data_age_months'] is not None else '—'} mes(es)",
                update_date,
            ]
        )
    services_table = Table(service_rows, repeatRows=1, colWidths=[155, 72, 62, 95, 75, 85])
    services_table.setStyle(TableStyle(_pdf_table_style(colors, font_size=8.0)))
    story.append(services_table)

    def draw_header(canvas, document) -> None:
        """Draw a consistent admin municipal SIGAM header on each page."""

        canvas.saveState()
        canvas.setFillColor(colors.HexColor("#1A3A6B"))
        canvas.rect(0, letter[1] - 44, letter[0], 44, fill=1, stroke=0)
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 12)
        canvas.drawString(46, letter[1] - 28, "SIGAM · Reporte municipal interno")
        canvas.setFont("Helvetica", 9)
        canvas.drawRightString(letter[0] - 46, letter[1] - 28, f"Corte {snapshot.label}")
        canvas.restoreState()

    doc.build(story, onFirstPage=draw_header, onLaterPages=draw_header)
    return buffer.getvalue()


def _admin_national_pdf_bytes(snapshot: SnapshotContext, view: dict[str, Any]) -> bytes:
    """Generate the formal admin national PDF report.

    Args:
        snapshot: Snapshot context.
        view: Administrator national view model.

    Returns:
        PDF bytes.
    """

    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.65 * inch,
        rightMargin=0.65 * inch,
        topMargin=0.95 * inch,
        bottomMargin=0.65 * inch,
        pageCompression=0,
    )
    styles = getSampleStyleSheet()
    styles.add(
        ParagraphStyle(
            name="SigamBodyAdmin",
            parent=styles["BodyText"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=13,
            textColor=colors.HexColor("#334155"),
            alignment=TA_LEFT,
        )
    )
    level_summary = " · ".join(
        f"{level}: {count}" for level, count in view["distribution_by_level"].items()
    )
    story = [
        Paragraph("Reporte nacional interno SIGAM", styles["Title"]),
        Spacer(1, 8),
        Paragraph(
            (
                "Resumen interno para Contraloría con ranking nacional, promedio por servicio "
                "y distribución de madurez en el período seleccionado."
            ),
            styles["SigamBodyAdmin"],
        ),
        Spacer(1, 10),
        Paragraph(f"<b>Período:</b> {snapshot.label}", styles["SigamBodyAdmin"]),
        Paragraph(
            f"<b>Municipalidades consideradas:</b> {view['total_municipalities']}",
            styles["SigamBodyAdmin"],
        ),
        Paragraph(
            f"<b>Promedio nacional:</b> {view['average_score'] * 100:.2f}%",
            styles["SigamBodyAdmin"],
        ),
        Paragraph(f"<b>Distribución por nivel:</b> {level_summary}", styles["SigamBodyAdmin"]),
        Spacer(1, 10),
    ]

    service_rows = [["Servicio", "Nivel predominante", "Puntaje promedio"]]
    for service in view["service_summaries"]:
        service_rows.append(
            [
                service["service_name"],
                service["predominant_level"],
                f"{service['puntaje_pct']:.2f}%",
            ]
        )
    services_table = Table(service_rows, repeatRows=1, colWidths=[250, 130, 110])
    services_table.setStyle(TableStyle(_pdf_table_style(colors, font_size=8.3)))
    story.extend(
        [
            Paragraph("Promedio por servicio", styles["Heading2"]),
            Spacer(1, 6),
            services_table,
            PageBreak(),
            Paragraph("Ranking nacional visible", styles["Heading2"]),
            Spacer(1, 6),
        ]
    )

    ranking_rows = [["Posición", "Municipalidad", "Provincia", "Región", "Nivel", "Puntaje"]]
    for municipality in view["municipalities"][:28]:
        ranking_rows.append(
            [
                municipality["position"],
                municipality["municipality"]["nombre"],
                municipality["municipality"].get("provincia") or "—",
                municipality["municipality"].get("region") or "—",
                municipality["level"],
                f"{municipality['puntaje_pct']:.2f}%",
            ]
        )
    ranking_table = Table(ranking_rows, repeatRows=1, colWidths=[48, 150, 100, 88, 80, 64])
    ranking_table.setStyle(TableStyle(_pdf_table_style(colors, font_size=8.0)))
    story.append(ranking_table)

    def draw_header(canvas, document) -> None:
        """Draw a consistent admin national SIGAM header on each page."""

        canvas.saveState()
        canvas.setFillColor(colors.HexColor("#1A3A6B"))
        canvas.rect(0, letter[1] - 44, letter[0], 44, fill=1, stroke=0)
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 12)
        canvas.drawString(46, letter[1] - 28, "SIGAM · Reporte nacional interno")
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

    from reportlab.lib import colors
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    from reportlab.lib.units import inch
    from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

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
    distribution_chart = _plotly_figure_to_reportlab_image(
        distribucion_niveles_pie(report["distribution"], height=340),
        width_inches=5.8,
        height_inches=3.2,
    )
    service_frame = _build_service_maturity_frame(
        [
            {
                "service_name": service["service_name"],
                "level": service["predominant_level"],
            }
            for service in report["service_summaries"]
        ]
    )
    service_chart = _plotly_figure_to_reportlab_image(
        madurez_servicios_horizontal(
            service_frame,
            height=max(360, len(service_frame) * 28 + 120),
            prefer_inside_text=True,
            margin_left=210,
            margin_right=90,
        ),
        width_inches=6.9,
        height_inches=4.2,
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
            distribution_chart,
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
            service_chart,
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


