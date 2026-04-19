"""Advanced analytics view for the Contraloria portal."""

# views/admin_analysis.py — Análisis avanzado: geoespacial, clústeres, correlación, SEM

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from components.ui import page_header, alert_box
from components.charts import mapa_costa_rica, cluster_chart
from data.db_layer import get_ranking, get_scores_por_servicio_nacional, get_historial_nacional
ORDEN_NIVELES = ["Inicial", "Básico", "Intermedio", "Avanzado", "Optimizando"]

def show():
    """Render the advanced analytics page.

    The page reads national ranking data, creates geospatial, cluster,
    correlation, historical trend, and SEM analyses, and writes the resulting
    controls and charts to the active Streamlit page.
    """

    page_header("Análisis Avanzado", "Geoespacial · Clústeres · Correlación · Tendencias · Modelos estructurales", "🔬")

    ranking = get_ranking()
    df = pd.DataFrame(ranking)
    df["puntaje_pct"] = df["score_total"] * 100

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "🗺️ Mapa Geoespacial",
        "🔵 Análisis de Clústeres",
        "📊 Correlación",
        "📈 Tendencias Históricas",
        "🔗 Modelo Estructural (SEM)",
    ])

    # ─── TAB 1: MAPA GEOESPACIAL ──────────────────────────────────────────────
    with tab1:
        st.markdown("##### Distribución geoespacial del IGSM — Costa Rica 2025")
        st.caption("Cada punto representa una municipalidad. El tamaño indica el puntaje y el color el nivel de madurez.")

        col_f1, col_f2 = st.columns(2)
        with col_f1:
            var_mapa = st.selectbox(
                "Variable a visualizar",
                ["Nivel de madurez", "Puntaje IGSM", "Región"],
                key="var_mapa"
            )
        with col_f2:
            filtro_niv_map = st.multiselect(
                "Filtrar por nivel",
                ORDEN_NIVELES,
                default=ORDEN_NIVELES,
                key="filtro_map"
            )

        df_map = df[df["nivel"].isin(filtro_niv_map)].copy()

        try:
            fig_mapa = mapa_costa_rica(df_map)
            st.plotly_chart(fig_mapa, use_container_width=True)
        except Exception:
            # Fallback sin mapbox
            fig_mapa = px.scatter(
                df_map, x="lon", y="lat",
                color="nivel",
                color_discrete_map={
                    "Inicial": "#DC3545", "Básico": "#FD7E14",
                    "Intermedio": "#2196F3", "Avanzado": "#20C997", "Optimizando": "#7B2FBE"
                },
                size="puntaje_pct", size_max=20,
                hover_name="municipalidad",
                hover_data={"puntaje_pct": ":.1f", "nivel": True, "lat": False, "lon": False},
                category_orders={"nivel": ORDEN_NIVELES},
                labels={"lon": "Longitud", "lat": "Latitud"},
            )
            fig_mapa.update_layout(height=450, margin=dict(t=20, b=20))
            st.plotly_chart(fig_mapa, use_container_width=True)

        # Estadísticas por región
        st.markdown("##### Estadísticas por región")
        df_reg = df.groupby("region").agg(
            Municipalidades=("municipalidad", "count"),
            Promedio_Puntaje=("puntaje_pct", "mean"),
            Max_Puntaje=("puntaje_pct", "max"),
            Min_Puntaje=("puntaje_pct", "min"),
        ).round(1).reset_index()
        df_reg.columns = ["Región", "Municipalidades", "Promedio (%)", "Máximo (%)", "Mínimo (%)"]
        st.dataframe(df_reg.set_index("Región"), use_container_width=True)

    # ─── TAB 2: CLÚSTERES ────────────────────────────────────────────────────
    with tab2:
        st.markdown("##### Agrupamiento de municipalidades por perfil de desempeño")
        st.caption("K-Means clustering basado en puntajes por servicio para identificar patrones similares.")

        n_clusters = st.slider("Número de grupos (clústeres)", 2, 6, 4, key="n_clusters")

        try:
            from sklearn.cluster import KMeans
            import numpy as np

            # Preparar features de servicios
            serv_cols = list(ranking[0]["servicios"].keys())
            X_data = []
            for m in ranking:
                row = [m["servicios"].get(s, 0) for s in serv_cols]
                X_data.append(row)

            X = np.array(X_data)
            km = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            clusters = km.fit_predict(X)

            df["cluster"] = [f"Grupo {c+1}" for c in clusters]

            # PCA para visualizar en 2D
            from sklearn.decomposition import PCA
            pca = PCA(n_components=2, random_state=42)
            coords = pca.fit_transform(X)
            df["pca_x"] = coords[:, 0]
            df["pca_y"] = coords[:, 1]

            fig_cluster = px.scatter(
                df, x="pca_x", y="pca_y",
                color="cluster",
                symbol="nivel",
                hover_name="municipalidad",
                hover_data={"puntaje_pct": ":.1f", "nivel": True, "region": True, "pca_x": False, "pca_y": False},
                color_discrete_sequence=px.colors.qualitative.Bold,
                labels={"pca_x": "Componente Principal 1", "pca_y": "Componente Principal 2"},
            )
            fig_cluster.update_traces(marker=dict(size=10, opacity=0.85))
            fig_cluster.update_layout(height=420, margin=dict(t=20, b=20))
            st.plotly_chart(fig_cluster, use_container_width=True)

            # Tabla de grupos
            st.markdown("##### Caracterización de grupos")
            for g in sorted(df["cluster"].unique()):
                df_g = df[df["cluster"] == g]
                avg = df_g["puntaje_pct"].mean()
                nivel_pred = df_g["nivel"].value_counts().idxmax()
                with st.expander(f"{g} · {len(df_g)} municipalidades · Promedio {avg:.1f}% · Nivel predominante: {nivel_pred}"):
                    st.write(", ".join(sorted(df_g["municipalidad"].tolist())))

        except ImportError:
            alert_box("scikit-learn no está instalado. Instale con: pip install scikit-learn", "warning", "⚠️")
            fig_c = cluster_chart(df)
            st.plotly_chart(fig_c, use_container_width=True)

    # ─── TAB 3: CORRELACIÓN ──────────────────────────────────────────────────
    with tab3:
        st.markdown("##### Correlación entre servicios y puntaje global")
        st.caption("Identifica qué servicios tienen mayor influencia en el IGSM total.")

        try:
            import numpy as np
            serv_cols = list(ranking[0]["servicios"].keys())
            nombres_cortos = {
                "Recolección, depósito y tratamiento de residuos sólidos": "Recolección",
                "Aseo de vías y sitios públicos":   "Aseo Vías",
                "Urbanismo e infraestructura":      "Urbanismo",
                "Red vial cantonal":                "Red Vial",
                "Servicios sociales y complementarios": "Ss. Sociales",
                "Servicios educativos, culturales y deportivos": "Educativos",
                "Alcantarillado pluvial":            "Alcantarillado",
                "Agua potable":                     "Agua Potable",
                "Zona Marítimo Terrestre":           "ZMT",
                "Seguridad y vigilancia":            "Seguridad",
            }

            corr_data = {}
            for serv in serv_cols:
                vals = [m["servicios"].get(serv, 0) for m in ranking]
                scores = [m["score_total"] for m in ranking]
                corr = np.corrcoef(vals, scores)[0, 1]
                corr_data[nombres_cortos.get(serv, serv[:20])] = round(corr, 3)

            # Gráfico de correlación
            df_corr = pd.DataFrame([{"Servicio": k, "Correlación": v} for k, v in corr_data.items()])
            df_corr = df_corr.sort_values("Correlación", ascending=True)
            colors = ["#DC3545" if v < 0.5 else "#FD7E14" if v < 0.7 else "#28A745" for v in df_corr["Correlación"]]

            fig_corr = go.Figure(go.Bar(
                x=df_corr["Correlación"],
                y=df_corr["Servicio"],
                orientation="h",
                marker_color=colors,
                text=[f"{v:.3f}" for v in df_corr["Correlación"]],
                textposition="outside",
            ))
            fig_corr.update_layout(
                height=380,
                xaxis=dict(range=[0, 1.1], title="Coeficiente de correlación con IGSM total"),
                yaxis=dict(title=""),
                margin=dict(t=20, b=20, l=20, r=60),
                paper_bgcolor="white",
                plot_bgcolor="#FAFBFD",
            )
            st.plotly_chart(fig_corr, use_container_width=True)

            # Heatmap de correlación entre servicios
            st.markdown("##### Matriz de correlación entre servicios")
            matrix_data = {}
            for serv in serv_cols[:7]:  # Primeros 7 para claridad
                nc = nombres_cortos.get(serv, serv[:15])
                matrix_data[nc] = [m["servicios"].get(serv, 0) for m in ranking]
            df_matrix = pd.DataFrame(matrix_data)
            corr_matrix = df_matrix.corr()

            fig_hm = px.imshow(
                corr_matrix,
                color_continuous_scale="RdYlGn",
                zmin=-1, zmax=1,
                text_auto=".2f",
            )
            fig_hm.update_layout(height=400, margin=dict(t=20))
            st.plotly_chart(fig_hm, use_container_width=True)

        except Exception as e:
            st.error(f"Error en análisis de correlación: {e}")

    # ─── TAB 4: TENDENCIAS ───────────────────────────────────────────────────
    with tab4:
        st.markdown("##### Tendencia histórica del IGSM nacional (2022–2025)")
        hist_nal = get_historial_nacional()

        # Evolución del promedio
        anos = list(hist_nal.keys())
        promedios = [hist_nal[a]["promedio"] * 100 for a in anos]

        fig_tend = go.Figure()
        fig_tend.add_trace(go.Scatter(
            x=anos, y=promedios,
            mode="lines+markers+text",
            line=dict(color="#1A3A6B", width=3),
            marker=dict(size=10, color="#1A3A6B"),
            text=[f"{v:.1f}%" for v in promedios],
            textposition="top center",
            fill="tozeroy",
            fillcolor="rgba(26,58,107,0.08)",
            name="Promedio nacional",
        ))
        fig_tend.update_layout(
            height=280,
            xaxis=dict(title="Período"),
            yaxis=dict(title="Puntaje promedio (%)", range=[0, 70]),
            margin=dict(t=20, b=20),
            paper_bgcolor="white",
            plot_bgcolor="#FAFBFD",
        )
        st.plotly_chart(fig_tend, use_container_width=True)

        # Evolución por nivel
        st.markdown("##### Evolución de municipalidades por nivel de madurez")
        fig_evol = go.Figure()
        colores_n = {"Inicial": "#DC3545", "Básico": "#FD7E14", "Intermedio": "#2196F3", "Avanzado": "#20C997", "Optimizando": "#7B2FBE"}
        for nivel in ["Inicial", "Básico", "Intermedio"]:
            vals = [hist_nal[a].get(nivel, 0) for a in anos]
            fig_evol.add_trace(go.Scatter(
                x=anos, y=vals,
                mode="lines+markers",
                name=nivel,
                line=dict(color=colores_n[nivel], width=2),
                marker=dict(size=8),
            ))
        fig_evol.update_layout(
            height=280,
            xaxis=dict(title="Período"),
            yaxis=dict(title="N° municipalidades"),
            legend=dict(orientation="h", y=-0.3),
            margin=dict(t=20, b=20),
            paper_bgcolor="white",
            plot_bgcolor="#FAFBFD",
        )
        st.plotly_chart(fig_evol, use_container_width=True)

        # Insights clave
        st.markdown("##### Hallazgos clave (IGSM 2025)")
        hallazgos = [
            ("📉", "76% de municipalidades aún en niveles bajos (Básico e Inicial)", "#FD7E14"),
            ("⚠️", "Ninguna municipalidad ha alcanzado nivel Avanzado u Optimizando", "#DC3545"),
            ("📈", "Leve mejora: municipalidades en Intermedio pasaron de 16 (2023) a 20 (2025)", "#2196F3"),
            ("🔻", "Urbanismo y Servicios Sociales retrocedieron de Intermedio a Básico vs 2023", "#DC3545"),
            ("💧", "Alcantarillado pluvial es el servicio más débil (nivel Inicial) en 24 municipios", "#FD7E14"),
        ]
        for icono, texto, color in hallazgos:
            st.markdown(f"""
            <div style="border-left:3px solid {color}; padding:0.5rem 1rem; margin:0.3rem 0;
                        background:#FAFBFD; border-radius:0 6px 6px 0">
                {icono} {texto}
            </div>
            """, unsafe_allow_html=True)

    # ─── TAB 5: SEM ──────────────────────────────────────────────────────────
    with tab5:
        st.markdown("##### Modelo de Ecuaciones Estructurales (SEM)")
        st.caption("Análisis de las relaciones entre ejes de gestión y el puntaje IGSM global. Basado en coeficientes de regresión múltiple.")

        try:
            import numpy as np
            from sklearn.linear_model import LinearRegression

            # Calcular scores por eje
            eje_scores = {"Salubridad": [], "Desarrollo Urbano": [], "Servicios Sociales": []}
            igsm_scores = []

            for m in ranking:
                serv = m["servicios"]
                # Eje Salubridad
                sal = [serv.get("Recolección, depósito y tratamiento de residuos sólidos", 0),
                       serv.get("Aseo de vías y sitios públicos", 0),
                       serv.get("Alcantarillado pluvial", 0)]
                eje_scores["Salubridad"].append(np.mean(sal))

                # Eje Desarrollo Urbano
                urb = [serv.get("Urbanismo e infraestructura", 0),
                       serv.get("Red vial cantonal", 0),
                       serv.get("Zona Marítimo Terrestre", 0)]
                eje_scores["Desarrollo Urbano"].append(np.mean(urb))

                # Eje Servicios Sociales
                soc = [serv.get("Servicios sociales y complementarios", 0),
                       serv.get("Servicios educativos, culturales y deportivos", 0),
                       serv.get("Agua potable", 0),
                       serv.get("Seguridad y vigilancia", 0)]
                eje_scores["Servicios Sociales"].append(np.mean(soc))

                igsm_scores.append(m["score_total"])

            X_sem = np.column_stack([eje_scores["Salubridad"], eje_scores["Desarrollo Urbano"], eje_scores["Servicios Sociales"]])
            y_sem = np.array(igsm_scores)

            reg = LinearRegression().fit(X_sem, y_sem)
            coefs = reg.coef_
            r2 = reg.score(X_sem, y_sem)

            # Diagrama de caminos (path diagram)
            fig_sem = go.Figure()

            # Nodos
            nodos = {
                "Salubridad Pública":   (0.1, 0.75),
                "Desarrollo Urbano":    (0.1, 0.45),
                "Servicios Sociales":   (0.1, 0.15),
                "IGSM Total":          (0.7, 0.45),
            }
            for nombre, (x, y) in nodos.items():
                color_n = "#1A3A6B" if nombre == "IGSM Total" else "#2196F3"
                fig_sem.add_shape(type="rect",
                    x0=x-0.12, y0=y-0.08, x1=x+0.12, y1=y+0.08,
                    fillcolor=color_n, line=dict(color="white", width=2),
                )
                fig_sem.add_annotation(
                    x=x, y=y, text=f"<b>{nombre}</b>",
                    showarrow=False, font=dict(color="white", size=11),
                )

            # Flechas con coeficientes
            ejes_sem = ["Salubridad Pública", "Desarrollo Urbano", "Servicios Sociales"]
            for i, eje_n in enumerate(ejes_sem):
                x0, y0 = nodos[eje_n]
                x1, y1 = nodos["IGSM Total"]
                coef = coefs[i]
                color_a = "#28A745" if coef > 0.3 else "#FD7E14"
                fig_sem.add_annotation(
                    x=x1-0.12, y=y1+(y0-y1)*0.5,
                    ax=x0+0.12, ay=y0,
                    xref="x", yref="y", axref="x", ayref="y",
                    arrowhead=2, arrowsize=1.5, arrowwidth=2, arrowcolor=color_a,
                    text=f"β={coef:.3f}", showarrow=True,
                    font=dict(size=11, color=color_a),
                )

            fig_sem.update_layout(
                height=400,
                xaxis=dict(range=[-0.05, 1.0], showgrid=False, zeroline=False, showticklabels=False),
                yaxis=dict(range=[-0.05, 1.0], showgrid=False, zeroline=False, showticklabels=False),
                margin=dict(t=30, b=20),
                paper_bgcolor="white",
                plot_bgcolor="white",
            )
            st.plotly_chart(fig_sem, use_container_width=True)

            # Métricas del modelo
            st.markdown("##### Métricas del modelo")
            cm1, cm2, cm3 = st.columns(3)
            with cm1:
                st.metric("R² del modelo", f"{r2:.4f}", help="Capacidad explicativa del modelo")
            with cm2:
                eje_max = ejes_sem[int(np.argmax(coefs))]
                st.metric("Eje con mayor peso", eje_max.split()[0])
            with cm3:
                st.metric("Coeficiente más alto", f"{max(coefs):.3f}")

            st.caption(f"El modelo explica el **{r2*100:.1f}%** de la varianza del IGSM total.")

        except ImportError:
            alert_box("scikit-learn no está instalado. Instale con: pip install scikit-learn --break-system-packages", "warning", "⚠️")
        except Exception as e:
            st.error(f"Error en modelo SEM: {e}")
