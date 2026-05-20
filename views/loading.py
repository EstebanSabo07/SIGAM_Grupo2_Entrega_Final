"""Interstitial loading view shown immediately after login."""

from __future__ import annotations

import time

import streamlit as st

from data.snapshot import AUDIENCE_ADMIN, AUDIENCE_MUNICIPAL, current_snapshot


def _resolve_loading_target() -> tuple[str, str]:
    """Resolve the pending destination page and role for the loading view.

    Returns:
        Tuple with destination page and target role.
    """

    role = st.session_state.get("loading_target_role") or st.session_state.get("rol") or "municipalidad"
    default_page = "admin_dashboard" if role == "admin" else "muni_home"
    page = st.session_state.get("pending_page") or default_page
    return page, role


def _loading_copy(target_role: str) -> tuple[str, str]:
    """Build the title and subtitle shown in the loading card.

    Args:
        target_role: Target portal role.

    Returns:
        Title and descriptive copy for the loading screen.
    """

    if target_role == "admin":
        return (
            "Cargando panel de Contraloría",
            "Estamos preparando el resumen nacional, la navegación interna y el contexto del período más reciente.",
        )
    return (
        "Cargando portal municipal",
        "Estamos preparando el panel municipal, el formulario y la información vigente para su municipalidad.",
    )


def _warm_session_context(target_role: str) -> None:
    """Warm lightweight session context before redirecting to the portal.

    Args:
        target_role: Target portal role.
    """

    if target_role == "admin":
        snapshot = current_snapshot(AUDIENCE_ADMIN)
    else:
        municipality_code = (
            st.session_state.get("municipalidad_codigo")
            or st.session_state.get("muni_codigo")
        )
        snapshot = current_snapshot(
            AUDIENCE_MUNICIPAL,
            municipality_code=municipality_code,
        )
    st.session_state["snapshot_year"] = snapshot.year
    st.session_state["snapshot_month"] = snapshot.month


def show() -> None:
    """Render the interstitial loading page and continue to the target page."""

    target_page, target_role = _resolve_loading_target()
    title, subtitle = _loading_copy(target_role)

    st.markdown(
        (
            '<div class="loading-shell"><div class="loading-card">'
            '<div class="loading-badge">SIGAM</div>'
            f'<div class="loading-title">{title}</div>'
            f'<div class="loading-copy">{subtitle}</div>'
            '</div></div>'
        ),
        unsafe_allow_html=True,
    )

    progress_placeholder = st.empty()
    status_placeholder = st.empty()
    for progress_value, message in [
        (28, "Validando la sesión activa..."),
        (64, "Preparando el contexto y período disponible..."),
        (100, "Abriendo el portal solicitado..."),
    ]:
        progress_placeholder.progress(progress_value)
        status_placeholder.caption(message)
        if progress_value == 64:
            _warm_session_context(target_role)
        time.sleep(0.1)

    st.caption("La transición es breve y solo organiza la carga inicial del portal.")
    st.session_state["page"] = target_page
    st.session_state.pop("pending_page", None)
    st.session_state.pop("loading_target_role", None)
    time.sleep(0.08)
    st.rerun()
