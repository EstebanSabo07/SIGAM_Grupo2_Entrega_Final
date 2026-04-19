"""Municipal IGSM form view."""

# views/muni_form.py — Formulario IGSM por servicio con guardado parcial

import streamlit as st
from components.ui import page_header, alert_box, progress_steps
from data.indicators import (
    ESTRUCTURA_IGSM, TIPO_BINARIO, TIPO_COBERTURA,
    TIPO_PORCENTAJE, TIPO_INFORMATIVO, TIPO_DECISION,
    get_servicios_para_municipalidad, clasificar_nivel,
)
from data.calculation import calcular_igsm_municipalidad, calcular_consistencia
from data.db_layer import save_responses, load_responses

def show():
    """Render the municipal IGSM form workflow.

    The page loads municipality context and previous responses from Streamlit
    session state, renders one applicable service at a time, updates in-memory
    form responses, and routes to the summary screen before submission.
    """

    nombre = st.session_state.get("municipalidad", "Municipalidad")
    diversificados = st.session_state.get("diversificados", [])

    page_header("Formulario IGSM 2025", f"{nombre} · Complete todos los servicios aplicables", "📋")

    # ── Inicializar respuestas en session_state (carga previas desde BD) ────────
    codigo = st.session_state.get("municipalidad_codigo", "")
    if "form_respuestas" not in st.session_state:
        previas = load_responses(codigo) if codigo else {}
        st.session_state["form_respuestas"] = previas
    if "form_servicio_actual" not in st.session_state:
        st.session_state["form_servicio_actual"] = 0

    servicios_dict = get_servicios_para_municipalidad(diversificados)
    servicios_lista = list(servicios_dict.items())
    total_servicios = len(servicios_lista)
    idx_actual = st.session_state["form_servicio_actual"]

    # ── Barra de progreso global ───────────────────────────────────────────────
    pct_completado = (idx_actual / total_servicios) * 100
    st.progress(int(pct_completado), text=f"Servicio {min(idx_actual+1, total_servicios)} de {total_servicios} · {pct_completado:.0f}% completado")

    # ── Navegación por pestañas de servicios ──────────────────────────────────
    nombres_servicios = [
        s[:35] + "..." if len(s) > 35 else s
        for s, _ in servicios_lista
    ]

    # ── Formulario del servicio actual ────────────────────────────────────────
    if idx_actual >= total_servicios:
        _mostrar_resumen(nombre, diversificados)
        return

    serv_nombre, serv_data = servicios_lista[idx_actual]
    eje_nombre = serv_data["eje"]
    agrupacion = serv_data["agrupacion"]

    # Encabezado del servicio
    agrup_color = "#1A3A6B" if agrupacion == "Básico" else "#E87722"
    st.markdown(f"""
    <div class="sigam-card-blue" style="margin-bottom:1rem">
        <div style="display:flex; justify-content:space-between; align-items:start">
            <div>
                <div style="font-size:0.75rem; opacity:0.7; margin-bottom:0.3rem">
                    Eje: {eje_nombre}
                </div>
                <div style="font-size:1.1rem; font-weight:600">{serv_nombre}</div>
            </div>
            <span style="background:{agrup_color}; color:white; padding:3px 10px; border-radius:20px;
                         font-size:0.78rem; font-weight:600">{agrupacion}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # ── Indicadores por etapa ─────────────────────────────────────────────────
    etapas_data = ESTRUCTURA_IGSM[eje_nombre]["servicios"][serv_nombre]["etapas"]

    for etapa, indicadores in etapas_data.items():
        peso = {"Planificación": "50%", "Ejecución": "30%", "Evaluación": "20%"}.get(etapa, "")
        with st.expander(f"📌 {etapa}  ·  peso {peso}", expanded=(etapa == "Planificación")):
            for ind in indicadores:
                _render_indicador(ind, serv_nombre)

    # ── Ayuda de consistencia en tiempo real ──────────────────────────────────
    respuestas_actuales = st.session_state.get("form_respuestas", {})
    consist = calcular_consistencia(respuestas_actuales, diversificados)
    if consist["n_inconsistencias"] > 0:
        with st.expander(f"⚠️ Se detectaron {consist['n_inconsistencias']} posible(s) inconsistencia(s)", expanded=False):
            for inc in consist["inconsistencias"]:
                color = "#DC3545" if inc["severidad"] == "Alta" else "#FFC107"
                st.markdown(f"""
                <div style="border-left:3px solid {color}; padding:0.5rem 1rem; margin:0.3rem 0; background:#FAFBFD">
                    <strong>{inc['tipo']}:</strong> {inc['descripcion']}
                    <span style="color:{color}; font-size:0.8rem; float:right">{inc['severidad']}</span>
                </div>
                """, unsafe_allow_html=True)

    # ── Navegación ────────────────────────────────────────────────────────────
    st.markdown("---")
    col_prev, col_mid, col_next = st.columns([1, 2, 1])

    with col_prev:
        if idx_actual > 0:
            if st.button("← Anterior", use_container_width=True):
                st.session_state["form_servicio_actual"] = idx_actual - 1
                st.rerun()

    with col_mid:
        # Puntaje preliminar
        if respuestas_actuales:
            try:
                calc = calcular_igsm_municipalidad(respuestas_actuales, diversificados)
                nivel = clasificar_nivel(calc["score_total"])
                st.markdown(f"""
                <div style="text-align:center; padding:0.5rem; background:#F0F4F8; border-radius:8px">
                    <span style="font-size:0.85rem; color:#6B7A90">Puntaje preliminar: </span>
                    <strong style="color:#1A3A6B">{calc['puntaje_porcentaje']}%</strong>
                    &nbsp;&nbsp;
                </div>
                """, unsafe_allow_html=True)
            except Exception:
                pass

    with col_next:
        es_ultimo = (idx_actual == total_servicios - 1)
        if es_ultimo:
            if st.button("📊 Ver resumen →", type="primary", use_container_width=True):
                st.session_state["form_servicio_actual"] = total_servicios
                st.rerun()
        else:
            if st.button("Siguiente →", type="primary", use_container_width=True):
                st.session_state["form_servicio_actual"] = idx_actual + 1
                st.rerun()

    # Guardar progreso
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        if st.button("💾 Guardar progreso", use_container_width=True):
            st.success("✅ Progreso guardado. Puede retomar más tarde.")
    with col_g2:
        if st.button("← Volver al inicio", use_container_width=True):
            st.session_state["page"] = "muni_home"
            st.rerun()


def _render_indicador(ind: dict, serv_nombre: str):
    """Render one indicator input according to its configured type.

    Args:
        ind: Indicator metadata dictionary.
        serv_nombre: Service name that owns the indicator.
    """

    codigo = ind["codigo"]
    nombre = ind["nombre"]
    tipo   = ind["tipo"]
    key    = f"ind_{codigo}"

    # Valor actual guardado
    val_actual = st.session_state["form_respuestas"].get(codigo, None)

    st.markdown(f"""
    <div class="indicator-block">
        <div class="indicator-code">{codigo}</div>
        <div class="indicator-name">{nombre}</div>
    </div>
    """, unsafe_allow_html=True)

    if tipo == TIPO_INFORMATIVO:
        st.caption("ℹ️ Indicador informativo — no tiene puntuación asignada")
        val = st.text_input("Ingrese la información (opcional)", key=key + "_info", value="" if val_actual is None else str(val_actual))
        st.session_state["form_respuestas"][codigo] = val
        return

    if tipo == TIPO_BINARIO or tipo == TIPO_DECISION:
        opciones = ["No respondido", "Sí", "No"]
        idx_default = 0
        if val_actual == 1: idx_default = 1
        elif val_actual == 0 and val_actual is not None: idx_default = 2

        respuesta = st.radio(
            f"Respuesta:",
            opciones,
            index=idx_default,
            key=key,
            horizontal=True,
            label_visibility="collapsed",
        )
        if respuesta == "Sí":
            st.session_state["form_respuestas"][codigo] = 1
        elif respuesta == "No":
            st.session_state["form_respuestas"][codigo] = 0

    elif tipo == TIPO_COBERTURA:
        val = st.slider(
            "Cobertura promedio (%)",
            min_value=0, max_value=100,
            value=int((val_actual or 0) * 100),
            key=key,
            help="Ingrese el porcentaje promedio de cobertura del servicio en los distritos",
        )
        # Convertir a puntaje según tabla CGR
        if val <= 25:   score_cob = 0.0
        elif val <= 50: score_cob = 0.25
        elif val <= 75: score_cob = 0.50
        else:           score_cob = 1.0
        st.session_state["form_respuestas"][codigo] = score_cob
        st.caption(f"Puntaje asignado: **{score_cob}** (tabla CGR: 0–25%→0 | 26–50%→0.25 | 51–75%→0.50 | 76–100%→1)")

    elif tipo == TIPO_PORCENTAJE:
        val = st.number_input(
            "Valor (%)",
            min_value=0.0, max_value=100.0,
            value=float((val_actual or 0) * 100),
            step=0.1,
            key=key,
            help="Ingrese el porcentaje según la fórmula del indicador",
        )
        st.session_state["form_respuestas"][codigo] = round(val / 100, 4)

    # Subida de evidencia si aplica
    if ind.get("evidencia"):
        doc_requerido = ind.get("doc", "Documento de respaldo")
        with st.expander(f"📎 Adjuntar evidencia obligatoria: {doc_requerido}"):
            archivo = st.file_uploader(
                "Seleccione el archivo",
                key=key + "_ev",
                type=["pdf", "docx", "jpg", "png", "xlsx"],
                label_visibility="collapsed",
            )
            if archivo:
                st.success(f"✅ Archivo cargado: {archivo.name}")
                st.session_state["form_respuestas"][codigo + "_ev"] = archivo.name
            elif st.session_state["form_respuestas"].get(codigo + "_ev"):
                st.info(f"📎 Evidencia guardada: {st.session_state['form_respuestas'][codigo + '_ev']}")


def _mostrar_resumen(nombre: str, diversificados: list):
    """Render the review and confirmation screen before submission.

    Args:
        nombre: Municipality display name.
        diversificados: Diversified service keys applicable to the municipality.
    """

    respuestas = st.session_state.get("form_respuestas", {})

    page_header("Resumen del Formulario", "Revise su información antes de enviar", "📊")

    # Calcular score final
    try:
        calc = calcular_igsm_municipalidad(respuestas, diversificados)
        consist = calcular_consistencia(respuestas, diversificados)

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(f"""<div class="kpi-card" style="border-top-color:#1A3A6B">
                <div class="kpi-value">{calc['puntaje_porcentaje']}%</div>
                <div class="kpi-label">Puntaje IGSM Preliminar</div>
            </div>""", unsafe_allow_html=True)
        with c2:
            from components.ui import nivel_badge
            st.markdown(f"""<div class="kpi-card" style="border-top-color:#E87722">
                <div class="kpi-value" style="font-size:1.3rem">{nivel_badge(calc['nivel'])}</div>
                <div class="kpi-label" style="margin-top:0.5rem">Nivel estimado</div>
            </div>""", unsafe_allow_html=True)
        with c3:
            color_consist = "#28A745" if consist["estado"] == "Consistente" else "#FFC107" if consist["estado"] == "Alerta" else "#DC3545"
            st.markdown(f"""<div class="kpi-card" style="border-top-color:{color_consist}">
                <div class="kpi-value" style="color:{color_consist}">{consist['estado']}</div>
                <div class="kpi-label">Índice de consistencia</div>
            </div>""", unsafe_allow_html=True)

        if consist["n_inconsistencias"] > 0:
            alert_box(
                f"Se encontraron {consist['n_inconsistencias']} inconsistencia(s) en sus respuestas. "
                "Revise antes de enviar para evitar observaciones de la Contraloría.",
                "warning", "⚠️"
            )

        # Score por servicio
        st.markdown("#### Puntaje por servicio")
        servicios = get_servicios_para_municipalidad(diversificados)
        cols_s = st.columns(2)
        for i, (serv_nombre, serv_data) in enumerate(servicios.items()):
            sc = calc["servicios"].get(serv_nombre, {}).get("score", 0)
            nivel_s = clasificar_nivel(sc)
            from components.ui import nivel_badge as nb
            with cols_s[i % 2]:
                st.markdown(f"""
                <div style="display:flex; justify-content:space-between; align-items:center;
                            padding:0.6rem 1rem; border:1px solid #E8EDF4; border-radius:6px; margin-bottom:0.4rem; background:white">
                    <span style="font-size:0.85rem; color:#1A2636">{serv_nombre[:45]}</span>
                    <span>{nb(nivel_s)}&nbsp;<strong>{sc*100:.0f}%</strong></span>
                </div>
                """, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"Error al calcular: {e}")

    st.markdown("---")
    alert_box(
        "Una vez enviado, no podrá modificar el formulario sin autorización de la Contraloría. "
        "Asegúrese de que toda la información sea correcta.",
        "warning", "⚠️"
    )

    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("← Revisar respuestas", use_container_width=True):
            st.session_state["form_servicio_actual"] = 0
            st.rerun()
    with col_b:
        if st.button("✅ Confirmar y enviar a la Contraloría", type="primary", use_container_width=True):
            # Guardar respuestas en la base de datos
            try:
                codigo_muni = st.session_state.get("municipalidad_codigo", "")
                if codigo_muni:
                    save_responses(codigo_muni, st.session_state["form_respuestas"])
            except Exception as e:
                st.warning(f"Aviso: no se pudo guardar en BD: {e}")
            st.session_state["formulario_enviado"] = True
            st.session_state["form_resultado"] = calc
            st.success("🎉 ¡Formulario enviado exitosamente! Su información fue recibida por la Contraloría General.")
            st.balloons()
            import time; time.sleep(2)
            st.session_state["page"] = "muni_results"
            st.rerun()
