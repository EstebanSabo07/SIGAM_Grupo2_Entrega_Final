"""Municipal navigable IGSM form view."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import streamlit as st

from components.ui import page_header
from data.catalog_service import get_form_tree
from data.response_service import get_section_responses, save_section_changes
from data.snapshot import AUDIENCE_MUNICIPAL, current_snapshot


STAGE_ORDER = {"Planificación": 0, "Ejecución": 1, "Evaluación": 2}


@st.dialog("Cambios sin guardar")
def _render_unsaved_changes_dialog(
    municipality_code: str,
    current_service: dict[str, Any],
    snapshot: Any,
) -> None:
    """Render a single modal for unsaved changes before changing service.

    Args:
        municipality_code: Municipal code.
        current_service: Active service descriptor.
        snapshot: Snapshot context.
    """

    st.write(
        "Tiene cambios sin guardar en este servicio. Elija una acción para continuar."
    )
    c1, c2, c3 = st.columns(3)
    with c1:
        if st.button("Guardar y continuar", type="primary", width="stretch"):
            saved_rows = 0
            errors: list[str] = []
            for stage in current_service["stages"]:
                section_id = stage["section_id"]
                if not _is_dirty(section_id):
                    continue
                result = save_section_changes(
                    municipality_code,
                    section_id,
                    st.session_state[_section_state_key(section_id, "buffer")],
                    {"actor_subject": municipality_code},
                    snapshot=snapshot,
                )
                if result["validation_errors"]:
                    errors.extend(result["validation_errors"])
                    break
                saved_rows += result["saved_rows"]
                _load_section_state(municipality_code, section_id, snapshot)

            if errors:
                for error in errors:
                    st.error(error)
            else:
                st.session_state["form_current_service"] = st.session_state["form_pending_service"]
                st.session_state["form_pending_service"] = None
                st.session_state["form_last_message"] = f"Se guardaron {saved_rows} cambio(s) en el servicio."
                st.rerun()
    with c2:
        if st.button("Descartar cambios", width="stretch"):
            for stage in current_service["stages"]:
                _load_section_state(municipality_code, stage["section_id"], snapshot)
            st.session_state["form_current_service"] = st.session_state["form_pending_service"]
            st.session_state["form_pending_service"] = None
            st.rerun()
    with c3:
        if st.button("Cancelar", width="stretch"):
            st.session_state["form_pending_service"] = None
            st.rerun()


def show() -> None:
    """Render the navigable municipal form with explicit saves."""

    municipality_code = st.session_state.get("municipalidad_codigo") or st.session_state.get("muni_codigo")
    municipality_name = st.session_state.get("municipalidad", "Municipalidad")
    if not municipality_code:
        st.error("No se encontró el código de la municipalidad en la sesión.")
        return

    snapshot = current_snapshot(AUDIENCE_MUNICIPAL, municipality_code=municipality_code)
    page_header(
        "Formulario SIGAM",
        (
            "Actualice la información vigente por servicio. El formulario usa el timestamp actual del servidor "
            "al guardar y organiza los indicadores por etapas del servicio."
        ),
        "📋",
    )
    form_tree = get_form_tree(municipality_code, snapshot)
    services = _build_service_sections(form_tree)
    if not services:
        st.warning("No se encontró el catálogo del formulario para esta municipalidad.")
        return

    services_by_code = {service["service_code"]: service for service in services}
    st.session_state["form_service_map"] = services_by_code
    if st.session_state.get("form_current_service") not in services_by_code:
        st.session_state["form_current_service"] = services[0]["service_code"]

    current_service = services_by_code[st.session_state["form_current_service"]]
    pending_service = st.session_state.get("form_pending_service")
    if pending_service and _service_has_dirty(current_service):
        _render_unsaved_changes_dialog(municipality_code, current_service, snapshot)
    elif pending_service and not _service_has_dirty(current_service):
        st.session_state["form_current_service"] = pending_service
        st.session_state["form_pending_service"] = None
        st.rerun()

    if st.session_state.get("form_last_message"):
        st.success(st.session_state["form_last_message"])
        st.session_state["form_last_message"] = None

    nav_col, content_col = st.columns([1, 2.4])
    with nav_col:
        _render_service_list(services, current_service["service_code"])
    with content_col:
        _render_service_editor(municipality_code, municipality_name, current_service, snapshot)


def _build_service_sections(form_tree: dict[str, Any]) -> list[dict[str, Any]]:
    """Build service-oriented navigation metadata from the form tree.

    Args:
        form_tree: Nested catalog tree.

    Returns:
        Ordered service descriptors.
    """

    services = []
    for axis in form_tree["axes"]:
        for service in axis["services"]:
            stages = [
                {
                    "axis_name": axis["axis_name"],
                    "service_code": service["service_code"],
                    "service_name": service["service_name"],
                    "stage_name": stage["stage_name"],
                    "section_id": stage["section_id"],
                    "indicator_count": len(stage["indicators"]),
                }
                for stage in service["stages"]
            ]
            stages.sort(key=lambda item: STAGE_ORDER.get(item["stage_name"], 99))
            services.append(
                {
                    "axis_name": axis["axis_name"],
                    "service_code": service["service_code"],
                    "service_name": service["service_name"],
                    "stages": stages,
                    "indicator_count": sum(stage["indicator_count"] for stage in stages),
                }
            )
    return services


def _section_state_key(section_id: str, suffix: str) -> str:
    """Build a session-state key for section-specific state.

    Args:
        section_id: Encoded section identifier.
        suffix: State suffix.

    Returns:
        Streamlit session-state key.
    """

    return f"form_section::{suffix}::{section_id}"


def _value_widget_key(section_id: str, indicator_code: str) -> str:
    """Build the Streamlit widget key for an indicator value."""

    return f"form_value::{section_id}::{indicator_code}"


def _evidence_widget_version_key(section_id: str, indicator_code: str) -> str:
    """Build the session-state key for uploader versioning."""

    return f"form_evidence_version::{section_id}::{indicator_code}"


def _evidence_widget_key(section_id: str, indicator_code: str) -> str:
    """Build the Streamlit widget key for indicator evidence uploads."""

    version = st.session_state.get(_evidence_widget_version_key(section_id, indicator_code), 0)
    return f"form_evidence::{section_id}::{indicator_code}::{version}"


def _blank_widget_key(section_id: str, indicator_code: str) -> str:
    """Build the Streamlit widget key for the unanswered toggle."""

    return f"form_blank::{section_id}::{indicator_code}"


def _section_touched_key(section_id: str) -> str:
    """Build the session-state key used to track user edits per section.

    Args:
        section_id: Encoded section identifier.

    Returns:
        Streamlit session-state key.
    """

    return f"form_section::touched::{section_id}"


def _mark_section_touched(section_id: str) -> None:
    """Mark one section as user-edited in the current session.

    Args:
        section_id: Encoded section identifier.
    """

    st.session_state[_section_touched_key(section_id)] = True


def _load_section_state(municipality_code: str, section_id: str, snapshot: Any) -> None:
    """Load persisted section values into session state.

    Args:
        municipality_code: Municipal code.
        section_id: Encoded section identifier.
        snapshot: Snapshot context.
    """

    section = get_section_responses(municipality_code, section_id, snapshot)
    payload = {
        indicator["indicator_code"]: {
            "value": indicator.get("value"),
            "evidence_files": deepcopy(indicator.get("evidence_files", [])),
        }
        for indicator in section["indicators"]
    }
    st.session_state[_section_state_key(section_id, "catalog")] = section
    st.session_state[_section_state_key(section_id, "buffer")] = deepcopy(payload)
    st.session_state[_section_state_key(section_id, "saved")] = deepcopy(payload)
    st.session_state[_section_touched_key(section_id)] = False
    for indicator in section["indicators"]:
        st.session_state[_evidence_widget_version_key(section_id, indicator["indicator_code"])] = (
            st.session_state.get(_evidence_widget_version_key(section_id, indicator["indicator_code"]), 0) + 1
        )
        _prime_widget_state(section_id, indicator)


def _ensure_section_state(municipality_code: str, section_id: str, snapshot: Any) -> None:
    """Ensure a section state is loaded in Streamlit session state.

    Args:
        municipality_code: Municipal code.
        section_id: Encoded section identifier.
        snapshot: Snapshot context.
    """

    if _section_state_key(section_id, "catalog") not in st.session_state:
        _load_section_state(municipality_code, section_id, snapshot)


def _prime_widget_state(section_id: str, indicator: dict[str, Any]) -> None:
    """Prime widget session state for a section indicator.

    Args:
        section_id: Encoded section identifier.
        indicator: Indicator metadata with current values.
    """

    code = indicator["indicator_code"]
    value_key = _value_widget_key(section_id, code)
    uploader_key = _evidence_widget_key(section_id, code)
    value = indicator.get("value")
    if indicator["indicator_type"] in {"binario", "decision"}:
        if value == 1:
            st.session_state[value_key] = "Sí"
        elif value == 0:
            st.session_state[value_key] = "No"
        else:
            st.session_state[value_key] = "Sin respuesta"
    else:
        st.session_state[value_key] = float(value * 100) if value is not None else 0.0
        st.session_state[_blank_widget_key(section_id, code)] = value is None
    _ = uploader_key


def _service_has_dirty(service: dict[str, Any]) -> bool:
    """Return whether any stage in a service has unsaved changes.

    Args:
        service: Service descriptor.

    Returns:
        ``True`` when at least one stage differs from its saved state.
    """

    return any(_section_has_unsaved_changes(stage["section_id"]) for stage in service["stages"])


def _can_navigate_without_prompt(current_service: dict[str, Any] | None) -> bool:
    """Return whether service navigation can proceed without the dialog.

    Args:
        current_service: Active service descriptor, if available.

    Returns:
        ``True`` when there are no unsaved changes that should block navigation.
    """

    return current_service is None or not _service_has_dirty(current_service)


def _section_has_unsaved_changes(section_id: str) -> bool:
    """Return whether a section has user edits that differ from saved values.

    Args:
        section_id: Encoded section identifier.

    Returns:
        ``True`` when the section was touched and is still dirty.
    """

    return bool(st.session_state.get(_section_touched_key(section_id), False)) and _is_dirty(section_id)


def _request_service_navigation(service_code: str) -> None:
    """Request navigation to another service, respecting unsaved changes.

    Args:
        service_code: Target service code.
    """

    if service_code == st.session_state.get("form_current_service"):
        return
    current_service = st.session_state.get("form_service_map", {}).get(
        st.session_state.get("form_current_service")
    )
    if _can_navigate_without_prompt(current_service):
        st.session_state["form_current_service"] = service_code
        st.session_state["form_pending_service"] = None
        st.rerun()
    st.session_state["form_pending_service"] = service_code


def _render_service_list(services: list[dict[str, Any]], current_service_code: str) -> None:
    """Render the selectable list of services.

    Args:
        services: Service descriptors.
        current_service_code: Active service code.
    """

    st.markdown("##### Servicios")
    for service in services:
        label = f"{service['service_name']} ({service['indicator_count']})"
        button_type = "primary" if service["service_code"] == current_service_code else "secondary"
        if st.button(
            label,
            key=f"service_button::{service['service_code']}",
            width="stretch",
            type=button_type,
        ):
            _request_service_navigation(service["service_code"])


def _render_service_editor(
    municipality_code: str,
    municipality_name: str,
    current_service: dict[str, Any],
    snapshot: Any,
) -> None:
    """Render the active service editor with stage tabs.

    Args:
        municipality_code: Municipal code.
        municipality_name: Municipality display name.
        current_service: Service descriptor in focus.
        snapshot: Snapshot context.
    """

    st.markdown(f"### {current_service['service_name']}")
    st.caption(
        f"{municipality_name} · {current_service['axis_name']} · Guardado con fecha/hora del servidor"
    )

    tabs = st.tabs(
        [
            f"{stage['stage_name']} ({stage['indicator_count']})"
            for stage in current_service["stages"]
        ]
    )
    for tab, stage in zip(tabs, current_service["stages"]):
        with tab:
            _ensure_section_state(municipality_code, stage["section_id"], snapshot)
            _render_stage_editor(municipality_code, snapshot, stage)


def _render_stage_editor(municipality_code: str, snapshot: Any, stage: dict[str, Any]) -> None:
    """Render one stage editor inside the service tabs.

    Args:
        municipality_code: Municipal code.
        snapshot: Snapshot context used for current-value resolution.
        stage: Stage descriptor.
    """

    section_id = stage["section_id"]
    section = st.session_state[_section_state_key(section_id, "catalog")]

    action_cols = st.columns(2)
    with action_cols[0]:
        if st.button(
            f"💾 Guardar {stage['stage_name']}",
            key=f"save_stage::{section_id}",
            type="primary",
            width="stretch",
        ):
            result = save_section_changes(
                municipality_code,
                section_id,
                st.session_state[_section_state_key(section_id, "buffer")],
                {"actor_subject": municipality_code},
                snapshot=snapshot,
            )
            if result["validation_errors"]:
                for error in result["validation_errors"]:
                    st.error(error)
            else:
                st.success(f"Se guardaron {result['saved_rows']} cambio(s) en la etapa.")
                _load_section_state(municipality_code, section_id, snapshot)
                st.rerun()
    with action_cols[1]:
        if st.button(
            "↺ Restaurar valores guardados",
            key=f"restore_stage::{section_id}",
            width="stretch",
        ):
            _load_section_state(municipality_code, section_id, snapshot)
            st.rerun()

    search = st.text_input(
        "Buscar indicador en esta etapa",
        key=f"form_search::{section_id}",
    )
    visible_indicators = [
        indicator
        for indicator in section["indicators"]
        if not search
        or search.lower() in indicator["indicator_name"].lower()
        or search.lower() in indicator["indicator_code"].lower()
    ]

    for indicator in visible_indicators:
        _render_indicator_editor(section_id, indicator)


def _render_indicator_editor(section_id: str, indicator: dict[str, Any]) -> None:
    """Render the editor controls for one indicator.

    Args:
        section_id: Encoded section identifier.
        indicator: Indicator metadata and current values.
    """

    code = indicator["indicator_code"]
    st.markdown(
        f"""
        <div class="indicator-block">
            <div class="indicator-code">{code}</div>
            <div class="indicator-name">{indicator['indicator_name']}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    value_key = _value_widget_key(section_id, code)
    current_payload = st.session_state[_section_state_key(section_id, "buffer")][code]

    if indicator["indicator_type"] in {"binario", "decision"}:
        answer = st.radio(
            "Respuesta",
            ["Sin respuesta", "Sí", "No"],
            key=value_key,
            horizontal=True,
            label_visibility="collapsed",
            on_change=_mark_section_touched,
            args=(section_id,),
        )
        if answer == "Sí":
            current_payload["value"] = 1.0
        elif answer == "No":
            current_payload["value"] = 0.0
        else:
            current_payload["value"] = None
    else:
        blank_key = _blank_widget_key(section_id, code)
        blank = st.checkbox(
            "Sin respuesta",
            key=blank_key,
            on_change=_mark_section_touched,
            args=(section_id,),
        )
        number = st.number_input(
            "Valor (%)",
            min_value=0.0,
            max_value=100.0,
            step=1.0,
            key=value_key,
            disabled=blank,
            on_change=_mark_section_touched,
            args=(section_id,),
        )
        current_payload["value"] = None if blank else round(number / 100, 4)

    if indicator["documentation"]:
        st.caption(f"Referencia metodológica: {indicator['documentation']}")

    if indicator["evidence_required"]:
        uploader_key = _evidence_widget_key(section_id, code)
        files = st.file_uploader(
            "Adjuntar evidencia",
            key=uploader_key,
            accept_multiple_files=True,
            type=["pdf", "docx", "jpg", "png", "xlsx"],
            on_change=_mark_section_touched,
            args=(section_id,),
        )
        if files:
            current_payload["evidence_files"] = [
                {
                    "file_name": file.name,
                    "file_type": getattr(file, "type", None),
                }
                for file in files
            ]
        saved_evidence = current_payload.get("evidence_files", [])
        if saved_evidence:
            st.caption(
                "Evidencias cargadas: "
                + ", ".join(item["file_name"] for item in saved_evidence if item.get("file_name"))
            )

    st.markdown("<br>", unsafe_allow_html=True)


def _is_dirty(section_id: str) -> bool:
    """Return whether a section buffer differs from its saved values.

    Args:
        section_id: Encoded section identifier.

    Returns:
        ``True`` when the staged payload differs from the saved payload.
    """

    current = st.session_state.get(_section_state_key(section_id, "buffer"), {})
    saved = st.session_state.get(_section_state_key(section_id, "saved"), {})
    return _normalized_payload(current) != _normalized_payload(saved)


def _normalized_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Normalize a section payload for equality comparisons.

    Args:
        payload: Section payload keyed by indicator code.

    Returns:
        Normalized payload.
    """

    normalized = {}
    for code, item in payload.items():
        normalized[code] = {
            "value": item.get("value"),
            "evidence_files": sorted(
                [
                    {
                        "file_name": evidence.get("file_name"),
                        "file_type": evidence.get("file_type"),
                    }
                    for evidence in item.get("evidence_files", [])
                ],
                key=lambda evidence: (evidence.get("file_name") or "", evidence.get("file_type") or ""),
            ),
        }
    return normalized
