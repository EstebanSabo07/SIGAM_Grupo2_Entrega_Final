"""Export and publication view for the Contraloria portal."""

# views/admin_export.py — Exportación de reportes y publicación del ranking

import io
from datetime import date

import pandas as pd
import streamlit as st

from components.ui import alert_box, page_header
from data.db_layer import (
    get_estadisticas_nacionales,
    get_historial_nacional,
    get_municipalidad_data,
    get_ranking,
    get_scores_por_servicio_nacional,
    load_responses,
)


# ── Helpers ──────────────────────────────────────────────────────────────────

def _nombre_corto(nombre: str) -> str:
    """Return the short display name for a service.

    Args:
        nombre: Full service name.

    Returns:
        Short service name when configured, otherwise the original name.
    """

    mapa = {
        "Recolección, depósito y tratamiento de residuos sólidos": "Recolección Residuos",
        "Aseo de vías y sitios públicos":                          "Aseo de Vías",
        "Planificación y control urbano":                          "Urbanismo",
        "Gestión vial":                                            "Red Vial",
        "Alcantarillado pluvial":                                  "Alcantarillado",
        "Servicios sociales y comunitarios":                       "Servicios Sociales",
        "Servicios educativos, culturales y deportivos":           "Servicios Educativos",
        "Acueductos y agua potable":                               "Agua Potable",
        "Zona marítimo terrestre":                                 "ZMT",
        "Seguridad vial y tránsito":                               "Seguridad Vial",
    }
    return mapa.get(nombre, nombre)


def _generar_excel_nacional(ranking: list, stats: dict) -> bytes:
    """Generate the national IGSM Excel report.

    Args:
        ranking: National ranking records.
        stats: National summary statistics.

    Returns:
        Excel workbook bytes.
    """

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:

        # ── Hoja 1: Ranking completo ──────────────────────────────────────────
        df_rank = pd.DataFrame([{
            "Posición":        m["posicion"],
            "Municipalidad":   m["municipalidad"],
            "Provincia":       m["provincia"],
            "Región":          m["region"],
            "Puntaje (%)":     m["puntaje_pct"],
            "Nivel":           m["nivel"],
            "Estado":          m["estado_envio"],
            "N° Respuestas":   m["n_respuestas"],
        } for m in ranking])
        df_rank.to_excel(writer, index=False, sheet_name="Ranking 2025")

        # ── Hoja 2: Estadísticas nacionales ───────────────────────────────────
        dist = stats["distribucion_niveles"]
        df_stats = pd.DataFrame([{
            "Indicador": k, "Valor": v
        } for k, v in {
            "Total municipalidades":      stats["total_municipalidades"],
            "Formularios enviados":       stats["enviados"],
            "Pendientes":                 stats["pendientes"],
            "Participación (%)":          stats["pct_participacion"],
            "Promedio nacional (%)":      round(stats["promedio_nacional"] * 100, 2),
            "Puntaje máximo (%)":         round(stats["max_score"] * 100, 2),
            "Puntaje mínimo (%)":         round(stats["min_score"] * 100, 2),
            "Nivel Inicial":              dist.get("Inicial", 0),
            "Nivel Básico":               dist.get("Básico", 0),
            "Nivel Intermedio":           dist.get("Intermedio", 0),
            "Nivel Avanzado":             dist.get("Avanzado", 0),
            "Nivel Optimizando":          dist.get("Optimizando", 0),
        }.items()])
        df_stats.to_excel(writer, index=False, sheet_name="Estadísticas Nacionales")

        # ── Hoja 3: Promedios por servicio ────────────────────────────────────
        prom_serv = get_scores_por_servicio_nacional()
        df_serv = pd.DataFrame([{
            "Servicio":             _nombre_corto(k),
            "Promedio nacional (%)": round(v * 100, 2),
        } for k, v in sorted(prom_serv.items(), key=lambda x: -x[1])])
        df_serv.to_excel(writer, index=False, sheet_name="Promedios por Servicio")

        # ── Hoja 4: Puntajes por etapa ────────────────────────────────────────
        etapas_rows = []
        for m in ranking:
            row = {
                "Municipalidad": m["municipalidad"],
                "Provincia":     m["provincia"],
                "Puntaje Total (%)": m["puntaje_pct"],
            }
            for etapa, val in m.get("etapas", {}).items():
                row[f"{etapa} (%)"] = round(val * 100, 2)
            etapas_rows.append(row)
        pd.DataFrame(etapas_rows).to_excel(writer, index=False, sheet_name="Puntajes por Etapa")

        # ── Hoja 5: Puntajes por servicio (detalle) ───────────────────────────
        serv_rows = []
        for m in ranking:
            row = {"Municipalidad": m["municipalidad"], "Provincia": m["provincia"]}
            for serv, val in m.get("servicios", {}).items():
                row[_nombre_corto(serv)] = round(val * 100, 2)
            serv_rows.append(row)
        pd.DataFrame(serv_rows).to_excel(writer, index=False, sheet_name="Puntajes por Servicio")

        # ── Hoja 6: Historial nacional ────────────────────────────────────────
        historial = get_historial_nacional()
        df_hist = pd.DataFrame([{
            "Año":              anio,
            "Promedio (%)":     round(datos["promedio"] * 100, 2),
            "Inicial":          datos.get("Inicial", 0),
            "Básico":           datos.get("Básico", 0),
            "Intermedio":       datos.get("Intermedio", 0),
            "Avanzado":         datos.get("Avanzado", 0),
            "Optimizando":      datos.get("Optimizando", 0),
        } for anio, datos in historial.items()])
        df_hist.to_excel(writer, index=False, sheet_name="Historial Nacional")

    output.seek(0)
    return output.read()


def _generar_excel_municipalidad(nombre: str) -> bytes | None:
    """Generate an individual municipality Excel report.

    Args:
        nombre: Municipality display name.

    Returns:
        Excel workbook bytes, or None when the municipality is unknown.
    """

    data = get_municipalidad_data(nombre)
    if data is None:
        return None

    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:

        # ── Hoja 1: Resumen ───────────────────────────────────────────────────
        df_resumen = pd.DataFrame([{
            "Campo": k, "Valor": v
        } for k, v in {
            "Municipalidad":     data["municipalidad"],
            "Provincia":         data["provincia"],
            "Región":            data["region"],
            "Puntaje total (%)": data["puntaje_pct"],
            "Nivel de madurez":  data["nivel"],
            "Posición nacional": f"#{data['posicion']} de 84",
            "Estado formulario": data["estado_envio"],
            "N° respuestas":     data["n_respuestas"],
            "Fecha generación":  date.today().strftime("%d/%m/%Y"),
        }.items()])
        df_resumen.to_excel(writer, index=False, sheet_name="Resumen")

        # ── Hoja 2: Puntajes por etapa ────────────────────────────────────────
        etapas = data.get("etapas", {})
        df_etapas = pd.DataFrame([{
            "Etapa":        etapa,
            "Puntaje (%)":  round(val * 100, 2),
        } for etapa, val in etapas.items()])
        df_etapas.to_excel(writer, index=False, sheet_name="Puntajes por Etapa")

        # ── Hoja 3: Puntajes por servicio ─────────────────────────────────────
        servicios = data.get("servicios", {})
        df_servicios = pd.DataFrame([{
            "Servicio":     _nombre_corto(serv),
            "Puntaje (%)":  round(val * 100, 2),
        } for serv, val in sorted(servicios.items(), key=lambda x: -x[1])])
        df_servicios.to_excel(writer, index=False, sheet_name="Puntajes por Servicio")

        # ── Hoja 4: Respuestas individuales ───────────────────────────────────
        respuestas = load_responses(data["codigo"])
        if respuestas:
            df_resp = pd.DataFrame([{
                "Código indicador": cod,
                "Valor":            val,
            } for cod, val in sorted(respuestas.items())])
            df_resp.to_excel(writer, index=False, sheet_name="Respuestas")

    output.seek(0)
    return output.read()


# ── Vista principal ───────────────────────────────────────────────────────────

def show():
    """Render the export and publication page.

    The page offers national and municipal downloads, preview tables, filtered
    CSV exports, and ranking publication controls backed by Streamlit session
    state.
    """

    page_header("Exportar & Reportes", "Descargue datos, genere informes y publique el ranking oficial", "📥")

    ranking = get_ranking()
    stats   = get_estadisticas_nacionales()

    tab1, tab2, tab3 = st.tabs(["📊 Exportar datos", "📄 Informes por municipalidad", "🔒 Publicación oficial"])

    # ─── TAB 1: EXPORTAR DATOS ───────────────────────────────────────────────
    with tab1:
        st.markdown("##### Exportar ranking completo")

        df = pd.DataFrame(ranking)
        df_export = df[["posicion", "municipalidad", "provincia", "region",
                        "puntaje_pct", "nivel", "estado_envio", "n_respuestas"]].copy()
        df_export.columns = ["Posición", "Municipalidad", "Provincia", "Región",
                              "Puntaje (%)", "Nivel", "Estado Formulario", "N° Respuestas"]

        col1, col2 = st.columns(2)
        with col1:
            csv = df_export.to_csv(index=False).encode("utf-8")
            st.download_button(
                "📥 Descargar CSV completo",
                data=csv,
                file_name="IGSM_2025_ranking_completo.csv",
                mime="text/csv",
                use_container_width=True,
            )
        with col2:
            try:
                excel_bytes = _generar_excel_nacional(ranking, stats)
                st.download_button(
                    "📊 Descargar Excel completo (6 hojas)",
                    data=excel_bytes,
                    file_name="IGSM_2025_informe_nacional.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True,
                )
            except Exception as e:
                st.error(f"Error generando Excel: {e}")

        st.markdown("---")
        st.markdown("##### Vista previa")
        st.dataframe(df_export.head(20), use_container_width=True)

        st.markdown("---")
        st.markdown("##### Exportar por filtros")
        c1, c2 = st.columns(2)
        with c1:
            region_exp = st.selectbox("Exportar por región", ["Todas"] + sorted(df["region"].dropna().unique().tolist()), key="exp_reg")
        with c2:
            nivel_exp = st.selectbox("Exportar por nivel", ["Todos", "Inicial", "Básico", "Intermedio", "Avanzado", "Optimizando"], key="exp_niv")

        df_filtrado = df.copy()
        if region_exp != "Todas":
            df_filtrado = df_filtrado[df_filtrado["region"] == region_exp]
        if nivel_exp != "Todos":
            df_filtrado = df_filtrado[df_filtrado["nivel"] == nivel_exp]

        csv_f = df_filtrado[["posicion", "municipalidad", "puntaje_pct", "nivel"]].to_csv(index=False).encode("utf-8")
        st.download_button(
            f"📥 Descargar {len(df_filtrado)} municipalidades",
            data=csv_f,
            file_name=f"IGSM_2025_{region_exp}_{nivel_exp}.csv",
            mime="text/csv",
        )

    # ─── TAB 2: INFORMES ─────────────────────────────────────────────────────
    with tab2:
        st.markdown("##### Informe individual por municipalidad")

        nombres_all = sorted([m["municipalidad"] for m in ranking])
        muni_informe = st.selectbox("Seleccione la municipalidad", nombres_all, key="muni_inf")

        data_m = next((m for m in ranking if m["municipalidad"] == muni_informe), None)
        if data_m:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Puntaje", f"{data_m['puntaje_pct']}%")
            c2.metric("Nivel", data_m["nivel"])
            c3.metric("Posición", f"#{data_m['posicion']}")
            c4.metric("Respuestas", data_m["n_respuestas"])

            st.markdown("**Puntaje por servicio:**")
            serv = data_m.get("servicios", {})
            if serv:
                df_serv = pd.DataFrame([{
                    "Servicio":     _nombre_corto(k),
                    "Puntaje (%)":  round(v * 100, 1),
                } for k, v in sorted(serv.items(), key=lambda x: -x[1])])
                st.dataframe(df_serv, use_container_width=True, hide_index=True)

            col_a, col_b = st.columns(2)
            with col_a:
                try:
                    excel_muni = _generar_excel_municipalidad(muni_informe)
                    if excel_muni:
                        st.download_button(
                            f"📊 Descargar informe Excel — {muni_informe}",
                            data=excel_muni,
                            file_name=f"Informe_{muni_informe.replace(' ', '_')}_IGSM_2025.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True,
                        )
                except Exception as e:
                    st.error(f"Error: {e}")

            with col_b:
                serv_csv = pd.DataFrame([{
                    "Servicio": _nombre_corto(k),
                    "Puntaje (%)": round(v * 100, 1),
                } for k, v in serv.items()]).to_csv(index=False).encode("utf-8")
                st.download_button(
                    f"📥 Descargar CSV — {muni_informe}",
                    data=serv_csv,
                    file_name=f"Informe_{muni_informe.replace(' ', '_')}_IGSM_2025.csv",
                    mime="text/csv",
                    use_container_width=True,
                )

        st.markdown("---")
        st.markdown("##### Resumen estadístico nacional")
        dist = stats["distribucion_niveles"]
        resumen_rows = [
            {"Indicador": "Total municipalidades evaluadas",  "Valor 2025": stats["total_municipalidades"]},
            {"Indicador": "Formularios enviados",             "Valor 2025": stats["enviados"]},
            {"Indicador": "Participación (%)",                "Valor 2025": stats["pct_participacion"]},
            {"Indicador": "Promedio nacional IGSM (%)",       "Valor 2025": round(stats["promedio_nacional"] * 100, 2)},
            {"Indicador": "Puntaje máximo (%)",               "Valor 2025": round(stats["max_score"] * 100, 2)},
            {"Indicador": "Puntaje mínimo (%)",               "Valor 2025": round(stats["min_score"] * 100, 2)},
            {"Indicador": "Nivel predominante",               "Valor 2025": max(dist, key=dist.get) if dist else "—"},
            {"Indicador": "En nivel Inicial",                 "Valor 2025": dist.get("Inicial", 0)},
            {"Indicador": "En nivel Básico",                  "Valor 2025": dist.get("Básico", 0)},
            {"Indicador": "En nivel Intermedio",              "Valor 2025": dist.get("Intermedio", 0)},
            {"Indicador": "En nivel Avanzado",                "Valor 2025": dist.get("Avanzado", 0)},
            {"Indicador": "En nivel Optimizando",             "Valor 2025": dist.get("Optimizando", 0)},
        ]
        df_resumen = pd.DataFrame(resumen_rows)
        st.dataframe(df_resumen.set_index("Indicador"), use_container_width=True)
        st.download_button(
            "📥 Descargar resumen CSV",
            data=df_resumen.to_csv(index=False).encode("utf-8"),
            file_name="Resumen_IGSM_2025.csv",
            mime="text/csv",
        )

    # ─── TAB 3: PUBLICACIÓN ──────────────────────────────────────────────────
    with tab3:
        st.markdown("##### Control de publicación del ranking oficial")
        alert_box(
            "La publicación oficial congela el ranking y lo hace visible para todas las municipalidades. "
            "Esta acción no puede deshacerse sin una nueva publicación.",
            "warning", "⚠️"
        )

        publicado   = st.session_state.get("ranking_publicado", False)
        fecha_pub   = st.session_state.get("fecha_publicacion", "—")

        if publicado:
            st.markdown(f"""
            <div class="alert-success">
                ✅ <strong>Ranking publicado el {fecha_pub}</strong><br>
                Las 84 municipalidades pueden consultar su posición y puntaje oficial.
            </div>
            """, unsafe_allow_html=True)
            if st.button("🔄 Despublicar (nueva revisión)", type="secondary"):
                st.session_state["ranking_publicado"] = False
                st.rerun()
        else:
            st.markdown("""
            <div class="alert-warning">
                ⏳ <strong>El ranking no ha sido publicado oficialmente.</strong><br>
                Las municipalidades solo pueden ver su propio progreso, no el ranking comparativo.
            </div>
            """, unsafe_allow_html=True)

            st.markdown("##### Verificación previa a la publicación")
            completados = stats["enviados"]
            total       = stats["total_municipalidades"]
            pct         = stats["pct_participacion"]

            st.markdown(f"""
            <div style="padding:1rem; background:#F0F4F8; border-radius:8px; margin:1rem 0">
                <div style="margin-bottom:0.5rem">
                    {completados}/{total} municipalidades han enviado su formulario ({pct}% participación)
                </div>
                <div style="background:#E8EDF4; height:10px; border-radius:5px">
                    <div style="background:#1A3A6B; width:{pct}%; height:10px; border-radius:5px"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            confirmar = st.checkbox("Confirmo que he revisado todos los formularios y deseo publicar el ranking oficial 2025")

            if st.button("🔓 Publicar Ranking Oficial 2025", type="primary", disabled=not confirmar):
                st.session_state["ranking_publicado"] = True
                st.session_state["fecha_publicacion"] = date.today().strftime("%d/%m/%Y")
                st.success("🎉 Ranking publicado exitosamente. Las municipalidades ya pueden ver sus resultados comparativos.")
                st.rerun()
