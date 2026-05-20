"""Login view for municipality and administrator demo access."""

# views/login.py — Acceso simplificado: municipalidad (código) o admin

from pathlib import Path

import streamlit as st

from data.municipalities import MUNICIPALIDADES, CODIGOS_ACCESO

ADMIN_USUARIO = "contraloria"
ADMIN_CLAVE   = "cgr2025"


def _start_loading_transition(target_page: str, target_role: str) -> None:
    """Queue an interstitial loading screen before entering the portal.

    Args:
        target_page: Destination page after the loading screen.
        target_role: Session role entering the portal.
    """

    st.session_state["pending_page"] = target_page
    st.session_state["loading_target_role"] = target_role
    st.session_state["page"] = "loading"
    st.query_params.clear()
    st.rerun()


def show() -> None:
    """Render the login page.

    The page authenticates demo municipal and administrator users, then updates
    Streamlit session state with the selected role, municipality context, and
    next page.
    """

    logo_cgr = Path(__file__).parent.parent / "assets" / "logo_cgr.svg"
    rol = st.session_state.get("rol_login", "municipalidad")

    # ── Layout centrado ───────────────────────────────────────────────────────
    _, col, _ = st.columns([1, 2, 1])
    with col:
        if logo_cgr.exists():
            st.image(str(logo_cgr), width=100)

        if rol == "municipalidad":
            st.markdown("## Acceso Municipal")
            st.markdown("Ingrese con el código asignado a su municipalidad.")
            st.markdown("<br>", unsafe_allow_html=True)

            nombres = [m["nombre"] for m in MUNICIPALIDADES]
            municipalidad = st.selectbox("Seleccione su municipalidad", [""] + nombres, key="sel_muni")

            codigo = st.text_input(
                "Código de acceso (4 dígitos)",
                type="password",
                placeholder="Ej. 0101",
                max_chars=4,
            )

            if st.button("Ingresar →", type="primary", width="stretch"):
                if not municipalidad:
                    st.error("Seleccione su municipalidad.")
                elif not codigo:
                    st.error("Ingrese el código de acceso.")
                else:
                    # Buscar código de la municipalidad seleccionada
                    muni_data = next((m for m in MUNICIPALIDADES if m["nombre"] == municipalidad), None)
                    if muni_data:
                        codigo_correcto = CODIGOS_ACCESO.get(muni_data["codigo"], "")
                        if codigo == codigo_correcto or codigo == "1234":  # 1234 = demo universal
                            st.session_state["rol"]          = "municipalidad"
                            st.session_state["municipalidad"]= municipalidad
                            st.session_state["muni_codigo"]  = muni_data["codigo"]
                            st.session_state["municipalidad_codigo"] = muni_data["codigo"]
                            st.session_state["diversificados"]= muni_data["diversificados"]
                            _start_loading_transition("muni_home", "municipalidad")
                        else:
                            st.error("Código incorrecto. Para la demo use: **1234**")
                    else:
                        st.error("Municipalidad no encontrada.")

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("""
            <div class="alert-info">
                💡 <strong>Modo Demo:</strong> Seleccione cualquier municipalidad y use el código <strong>1234</strong>
            </div>
            """, unsafe_allow_html=True)

        else:  # admin
            st.markdown("## Acceso Contraloría")
            st.markdown("Ingrese con sus credenciales institucionales.")
            st.markdown("<br>", unsafe_allow_html=True)

            usuario = st.text_input("Usuario", placeholder="contraloria")
            clave   = st.text_input("Contraseña", type="password", placeholder="••••••••")

            if st.button("Ingresar →", type="primary", width="stretch"):
                if usuario == ADMIN_USUARIO and clave == ADMIN_CLAVE:
                    st.session_state["rol"]  = "admin"
                    _start_loading_transition("admin_dashboard", "admin")
                else:
                    st.error("Credenciales incorrectas. Demo: **contraloria** / **cgr2025**")

            st.markdown("<br>", unsafe_allow_html=True)
            st.markdown("""
            <div class="alert-info">
                💡 <strong>Modo Demo:</strong> Usuario: <strong>contraloria</strong> · Contraseña: <strong>cgr2025</strong>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("---")
        if st.button("← Volver al inicio", width="content"):
            st.session_state["page"] = "landing"
            st.rerun()
