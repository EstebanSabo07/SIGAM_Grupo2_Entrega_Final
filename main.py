"""Streamlit entrypoint and session-state router for SIGAM."""

# main.py — SIGAM · Sistema Integrado de Gestión y Análisis Municipal
# Punto de entrada principal con enrutamiento basado en session_state

import streamlit as st

# ── Configuración de página ───────────────────────────────────────────────────
st.set_page_config(
    page_title="SIGAM — Sistema IGSM Costa Rica",
    page_icon="🏛️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Cargar CSS global ─────────────────────────────────────────────────────────
from components.ui import load_css, sidebar_muni, sidebar_admin
load_css()

# ── Estado inicial ────────────────────────────────────────────────────────────
if "page" not in st.session_state:
    st.session_state["page"] = "landing"
if "rol" not in st.session_state:
    st.session_state["rol"] = None

page = st.session_state.get("page", "landing")
rol  = st.session_state.get("rol")

# ── Enrutador principal ───────────────────────────────────────────────────────

# Páginas públicas (sin autenticación)
if page in ("landing", None):
    from views.landing import show
    show()

elif page == "login":
    from views.login import show
    show()

# Portal Municipalidad
elif rol == "municipalidad":
    nombre_muni = st.session_state.get("municipalidad", "Municipalidad")
    sidebar_muni(nombre_muni)

    if page == "muni_home":
        from views.muni_home import show
        show()
    elif page == "muni_form":
        from views.muni_form import show
        show()
    elif page == "muni_results":
        from views.muni_results import show
        show()
    else:
        st.session_state["page"] = "muni_home"
        st.rerun()

# Portal Contraloría / Admin
elif rol == "admin":
    sidebar_admin()

    if page == "admin_dashboard":
        from views.admin_dashboard import show
        show()
    elif page == "admin_municipalities":
        from views.admin_municipalities import show
        show()
    elif page == "admin_analysis":
        from views.admin_analysis import show
        show()
    elif page == "admin_weights":
        from views.admin_weights import show
        show()
    elif page == "admin_export":
        from views.admin_export import show
        show()
    else:
        st.session_state["page"] = "admin_dashboard"
        st.rerun()

# Sin sesión pero en página que requiere auth
else:
    st.session_state["page"] = "landing"
    st.rerun()
