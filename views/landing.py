"""Public landing page view for SIGAM."""

# views/landing.py — Página pública de presentación de SIGAM

import streamlit as st
import base64
from pathlib import Path

def _img_b64(path: Path, mime: str = "image/png") -> str:
    """Encode an image file as a data URI.

    Args:
        path: Image file path.
        mime: MIME type to include in the data URI.

    Returns:
        Base64 data URI for embedding in HTML.
    """

    with open(path, "rb") as f:
        return f"data:{mime};base64,{base64.b64encode(f.read()).decode()}"

def show():
    """Render the public landing page.

    The page displays the SIGAM introduction, project information, quick
    statistics, and navigation actions that update Streamlit session state for
    login routing.
    """

    assets = Path(__file__).parent.parent / "assets"
    logo_cgr  = assets / "logo_cgr.svg"
    logo_lead = assets / "logo_lead.png"

    # Preparar src de logos para el hero
    cgr_src  = _img_b64(logo_cgr,  "image/svg+xml") if logo_cgr.exists()  else ""
    lead_src = _img_b64(logo_lead, "image/png")     if logo_lead.exists() else ""

    logo_cgr_html = f'<img src="{cgr_src}" alt="CGR" style="height:48px; filter:brightness(0) invert(1); opacity:0.92;">' if cgr_src else ""
    logo_lead_html = f'<img src="{lead_src}" alt="LEAD University" style="height:52px; filter:brightness(0) invert(1); opacity:0.92;">' if lead_src else ""

    # ── Hero ──────────────────────────────────────────────────────────────────
    st.markdown(f"""
    <div class="landing-hero">
        <div class="landing-tag">BETA · IGSM 2025</div>
        <h1>SIGAM</h1>
        <div style="width:100%; text-align:center; font-size:1.15rem; font-weight:300;
                    color:rgba(255,255,255,0.9); margin:0.4rem 0 0.8rem;">
            Sistema Integrado de Gestión y Análisis Municipal
        </div>
        <div style="width:100%; text-align:center; font-size:1.05rem;
                    color:rgba(255,255,255,0.8); max-width:600px; margin:0 auto;">
            Plataforma centralizada para la digitalización y automatización del
            Índice de Gestión de Servicios Municipales de Costa Rica.
        </div>
        <div style="
            display:flex; align-items:center; justify-content:center;
            gap:2rem; margin-top:2rem; padding-top:1.5rem;
            border-top: 1px solid rgba(255,255,255,0.2);">
            {logo_cgr_html}
            <div style="width:1px; height:40px; background:rgba(255,255,255,0.25);"></div>
            {logo_lead_html}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Botones de acceso (centrados) ─────────────────────────────────────────
    _, col1, col2, _ = st.columns([1, 2, 2, 1])
    with col1:
        if st.button("🏛️  Soy una Municipalidad", use_container_width=True, type="primary"):
            st.session_state["rol_login"] = "municipalidad"
            st.session_state["page"] = "login"
            st.rerun()
    with col2:
        if st.button("🔍  Soy de la Contraloría", use_container_width=True):
            st.session_state["rol_login"] = "admin"
            st.session_state["page"] = "login"
            st.rerun()

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Qué es SIGAM ─────────────────────────────────────────────────────────
    st.markdown("### ¿Qué es SIGAM?")
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown("""
        <div class="sigam-card">
            <strong>📋 Para Municipalidades</strong><br><br>
            Completen el formulario del IGSM en línea, siguiendo exactamente la metodología
            oficial de la CGR. Guarden su progreso, suban evidencias y consulten sus
            resultados en tiempo real.
        </div>
        """, unsafe_allow_html=True)
        st.markdown("""
        <div class="sigam-card">
            <strong>✅ Validación automática</strong><br><br>
            El sistema detecta inconsistencias en las respuestas, compara con el historial
            y alerta sobre variaciones inusuales, reduciendo el sesgo de autocalificación.
        </div>
        """, unsafe_allow_html=True)
    with col_b:
        st.markdown("""
        <div class="sigam-card">
            <strong>📊 Para la Contraloría</strong><br><br>
            Dashboard nacional en tiempo real con ranking, análisis por región, gestión
            de pesos del índice, análisis avanzado (geoespacial, clústeres, tendencias)
            y exportación de reportes.
        </div>
        """, unsafe_allow_html=True)
        st.markdown("""
        <div class="sigam-card">
            <strong>📥 Reportes descargables</strong><br><br>
            Generación automática de informes individuales por municipalidad y reportes
            nacionales en PDF y Excel con un solo clic.
        </div>
        """, unsafe_allow_html=True)

    # ── Estadísticas rápidas ──────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("### Datos del IGSM 2025")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown("""<div class="kpi-card" style="border-top-color:#1A3A6B">
            <div class="kpi-value">84</div>
            <div class="kpi-label">Municipalidades evaluadas</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown("""<div class="kpi-card" style="border-top-color:#FD7E14">
            <div class="kpi-value">68%</div>
            <div class="kpi-label">En nivel Básico</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown("""<div class="kpi-card" style="border-top-color:#2196F3">
            <div class="kpi-value">159</div>
            <div class="kpi-label">Indicadores evaluados</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        st.markdown("""<div class="kpi-card" style="border-top-color:#20C997">
            <div class="kpi-value">10</div>
            <div class="kpi-label">Servicios municipales</div>
        </div>""", unsafe_allow_html=True)

    # ── Información del proyecto ──────────────────────────────────────────────
    st.markdown("---")
    st.markdown("""
    <div class="sigam-card" style="background:#F0F4F8; border:none;">
        <div style="display:flex; align-items:center; gap:2rem; flex-wrap:wrap;">
            <div style="flex:1; min-width:200px;">
                <div style="font-size:0.75rem; color:#6B7A90; text-transform:uppercase; letter-spacing:1px; margin-bottom:0.5rem;">
                    PROYECTO ACADÉMICO
                </div>
                <div style="font-size:1rem; font-weight:600; color:#1A3A6B; margin-bottom:0.3rem;">
                    Curso BBCD0001 – Análisis de Datos
                </div>
                <div style="color:#4A5568; font-size:0.9rem;">
                    <strong>Profesor:</strong> Dagoberto José Herrera Murillo<br>
                    <strong>Institución:</strong> LEAD University<br>
                    <strong>Colaboración:</strong> Contraloría General de la República de Costa Rica
                </div>
            </div>
            <div style="flex:1; min-width:200px;">
                <div style="font-size:0.75rem; color:#6B7A90; text-transform:uppercase; letter-spacing:1px; margin-bottom:0.5rem;">
                    EQUIPO DE DESARROLLO
                </div>
                <div style="color:#4A5568; font-size:0.9rem;">
                    Esteban Gutiérrez Saborío<br>
                    Jason Corrau Madrigal<br>
                    Robson Sthiffen Calvo Ortega
                </div>
            </div>
            <div style="flex:0.5; text-align:center; min-width:120px;">
                <div style="font-size:0.75rem; color:#6B7A90; margin-bottom:0.3rem;">PERÍODO</div>
                <div style="font-size:1.8rem; font-weight:700; color:#1A3A6B;">2025</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Footer ─────────────────────────────────────────────────────────────────
    st.markdown("<br>", unsafe_allow_html=True)
    st.caption("© 2025 · SIGAM · LEAD University · CGR Costa Rica")
