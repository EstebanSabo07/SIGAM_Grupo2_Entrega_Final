"""Plotly chart builders used by SIGAM views."""

# components/charts.py — Visualizaciones Plotly para SIGAM

import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

COLORES_NIVEL = {
    "Inicial":     "#DC3545",
    "Básico":      "#FD7E14",
    "Intermedio":  "#2196F3",
    "Avanzado":    "#20C997",
    "Optimizando": "#7B2FBE",
}
ORDEN_NIVELES = ["Inicial", "Básico", "Intermedio", "Avanzado", "Optimizando"]
COLOR_PRIMARY = "#1A3A6B"
COLOR_ACCENT  = "#E87722"

def _layout_base(fig, height=400):
    """Apply the shared SIGAM visual layout to a Plotly figure.

    Args:
        fig: Plotly figure to style.
        height: Figure height in pixels.

    Returns:
        The same Plotly figure with common layout properties applied.
    """

    fig.update_layout(
        height=height,
        margin=dict(t=30, b=40, l=20, r=20),
        paper_bgcolor="white",
        plot_bgcolor="#FAFBFD",
        font=dict(color="#1A2636", size=11),
        legend=dict(bgcolor="white", bordercolor="#E8EDF4", borderwidth=1),
    )
    return fig


def ranking_bar_chart(df: pd.DataFrame, top_n: int = 20) -> go.Figure:
    """Build a horizontal ranking chart for municipalities.

    Args:
        df: Ranking data with municipality, level, and total score columns.
        top_n: Number of municipalities to display from the top of the data.

    Returns:
        Plotly bar chart with municipalities grouped by maturity level.
    """

    df_top = df.head(top_n).copy()
    df_top["color"] = df_top["nivel"].map(COLORES_NIVEL)
    df_top["puntaje_pct"] = df_top["score_total"] * 100

    fig = go.Figure()
    for nivel in ORDEN_NIVELES:
        df_n = df_top[df_top["nivel"] == nivel]
        if df_n.empty:
            continue
        fig.add_trace(go.Bar(
            x=df_n["puntaje_pct"],
            y=df_n["municipalidad"],
            orientation="h",
            name=nivel,
            marker_color=COLORES_NIVEL[nivel],
            text=[f"{v:.1f}%" for v in df_n["puntaje_pct"]],
            textposition="outside",
            hovertemplate="<b>%{y}</b><br>Puntaje: %{x:.1f}%<extra></extra>",
        ))
    fig.update_layout(
        barmode="stack",
        xaxis=dict(range=[0, 105], title="Puntaje IGSM (%)"),
        yaxis=dict(autorange="reversed", title=""),
        legend=dict(title="Nivel", orientation="h", y=-0.15),
    )
    return _layout_base(fig, height=max(350, top_n * 22))


def distribucion_niveles_pie(distribucion: dict) -> go.Figure:
    """Build a donut chart for maturity-level distribution.

    Args:
        distribucion: Mapping from maturity level to municipality count.

    Returns:
        Plotly pie chart with the configured maturity colors.
    """

    labels = [k for k in ORDEN_NIVELES if k in distribucion]
    values = [distribucion[k] for k in labels]
    colors = [COLORES_NIVEL[k] for k in labels]

    fig = go.Figure(go.Pie(
        labels=labels,
        values=values,
        marker=dict(colors=colors, line=dict(color="white", width=2)),
        hole=0.45,
        textinfo="label+percent",
        hovertemplate="<b>%{label}</b><br>Municipalidades: %{value}<br>%{percent}<extra></extra>",
    ))
    fig.add_annotation(
        text=f"<b>{sum(values)}</b><br>munis",
        x=0.5, y=0.5, font=dict(size=14, color=COLOR_PRIMARY),
        showarrow=False,
    )
    return _layout_base(fig, height=320)


def radar_ejes(scores_eje: dict, nombre: str = "") -> go.Figure:
    """Build a radar chart for axis or service scores.

    Args:
        scores_eje: Mapping from axis or service name to score in the 0-1 range.
        nombre: Trace label to display when legends are enabled.

    Returns:
        Plotly polar scatter figure.
    """

    categorias = list(scores_eje.keys())
    valores = [v * 100 for v in scores_eje.values()]
    valores_cerrado = valores + [valores[0]]
    categorias_cerrado = categorias + [categorias[0]]

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=valores_cerrado,
        theta=categorias_cerrado,
        fill="toself",
        fillcolor=f"rgba(26,58,107,0.15)",
        line=dict(color=COLOR_PRIMARY, width=2),
        name=nombre,
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(range=[0, 100], tickfont=dict(size=9), gridcolor="#E8EDF4"),
            angularaxis=dict(tickfont=dict(size=10)),
        ),
        showlegend=False,
    )
    return _layout_base(fig, height=350)


def historico_lineas(historial_data: dict, nombre: str = "") -> go.Figure:
    """Build a line chart for historical IGSM scores.

    Args:
        historial_data: Mapping from period label to score in the 0-1 range.
        nombre: Trace label for the historical series.

    Returns:
        Plotly line chart with score percentages.
    """

    anos = list(historial_data.keys())
    valores = [v * 100 for v in historial_data.values()]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=anos, y=valores,
        mode="lines+markers",
        line=dict(color=COLOR_PRIMARY, width=3),
        marker=dict(size=9, color=COLOR_PRIMARY, line=dict(width=2, color="white")),
        fill="tozeroy",
        fillcolor="rgba(26,58,107,0.08)",
        name=nombre,
        hovertemplate="<b>%{x}</b><br>Puntaje: %{y:.1f}%<extra></extra>",
    ))
    fig.update_layout(
        xaxis=dict(title="Período"),
        yaxis=dict(title="Puntaje IGSM (%)", range=[0, 100]),
    )
    return _layout_base(fig, height=280)


def comparacion_servicios_bar(scores_servicios: dict, promedio_nacional: dict = None) -> go.Figure:
    """Build a service comparison bar chart.

    Args:
        scores_servicios: Mapping from service name to municipal score.
        promedio_nacional: Optional mapping from service name to national score.

    Returns:
        Plotly bar chart with optional national average markers.
    """

    nombres_cortos = {
        "Recolección, depósito y tratamiento de residuos sólidos": "Recolección",
        "Aseo de vías y sitios públicos":                          "Aseo Vías",
        "Urbanismo e infraestructura":                             "Urbanismo",
        "Red vial cantonal":                                       "Red Vial",
        "Servicios sociales y complementarios":                    "Servicios Sociales",
        "Servicios educativos, culturales y deportivos":           "Educativos/Culturales",
        "Alcantarillado pluvial":                                  "Alcantarillado",
        "Agua potable":                                            "Agua Potable",
        "Zona Marítimo Terrestre":                                 "ZMT",
        "Seguridad y vigilancia":                                  "Seguridad",
    }
    servicios = list(scores_servicios.keys())
    nombres  = [nombres_cortos.get(s, s) for s in servicios]
    valores  = [scores_servicios[s] * 100 for s in servicios]
    colores  = [COLORES_NIVEL[_nivel_por_score(v / 100)] for v in valores]

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=nombres, y=valores,
        marker_color=colores,
        text=[f"{v:.0f}%" for v in valores],
        textposition="outside",
        name="Municipalidad",
        hovertemplate="<b>%{x}</b><br>Puntaje: %{y:.1f}%<extra></extra>",
    ))
    if promedio_nacional:
        prom_vals = [promedio_nacional.get(s, 0) * 100 for s in servicios]
        fig.add_trace(go.Scatter(
            x=nombres, y=prom_vals,
            mode="markers",
            marker=dict(symbol="diamond", size=10, color=COLOR_ACCENT),
            name="Promedio nacional",
            hovertemplate="<b>Promedio %{x}</b><br>%{y:.1f}%<extra></extra>",
        ))
    fig.update_layout(
        xaxis=dict(title=""),
        yaxis=dict(title="Puntaje (%)", range=[0, 115]),
        legend=dict(orientation="h", y=-0.2),
        bargap=0.3,
    )
    return _layout_base(fig, height=380)


def mapa_costa_rica(df: pd.DataFrame) -> go.Figure:
    """Build a Costa Rica map colored by IGSM maturity level.

    Args:
        df: Municipality ranking data with latitude, longitude, score, and level.

    Returns:
        Plotly Mapbox scatter figure.
    """

    df = df.copy()
    df["puntaje_pct"] = df["score_total"] * 100
    df["nivel_num"] = df["nivel"].map({
        "Inicial": 1, "Básico": 2, "Intermedio": 3, "Avanzado": 4, "Optimizando": 5
    })

    fig = px.scatter_mapbox(
        df,
        lat="lat", lon="lon",
        color="nivel",
        color_discrete_map=COLORES_NIVEL,
        size="puntaje_pct",
        size_max=18,
        hover_name="municipalidad",
        hover_data={
            "puntaje_pct": ":.1f",
            "nivel": True,
            "provincia": True,
            "lat": False,
            "lon": False,
        },
        category_orders={"nivel": ORDEN_NIVELES},
        zoom=6.5,
        center={"lat": 9.95, "lon": -84.2},
        mapbox_style="carto-positron",
    )
    fig.update_layout(
        legend=dict(title="Nivel de Madurez", y=0.99, bgcolor="rgba(255,255,255,0.9)"),
        margin=dict(t=10, b=10, l=10, r=10),
    )
    return _layout_base(fig, height=480)


def heatmap_region_servicio(df: pd.DataFrame) -> go.Figure:
    """Build a heatmap of average service scores by region.

    Args:
        df: Ranking data containing region and nested service score values.

    Returns:
        Plotly heatmap figure.
    """

    nombres_cortos = {
        "Recolección, depósito y tratamiento de residuos sólidos": "Recolección",
        "Aseo de vías y sitios públicos":                          "Aseo Vías",
        "Urbanismo e infraestructura":                             "Urbanismo",
        "Red vial cantonal":                                       "Red Vial",
        "Servicios sociales y complementarios":                    "Ss. Sociales",
        "Servicios educativos, culturales y deportivos":           "Educativos",
    }
    regiones = sorted(df["region"].unique())
    servicios = list(nombres_cortos.keys())
    nombres_s = list(nombres_cortos.values())

    matrix = []
    for region in regiones:
        df_r = df[df["region"] == region]
        row = []
        for serv in servicios:
            vals = [m["servicios"].get(serv, 0) for m in df_r.to_dict("records")]
            row.append(round(sum(vals) / len(vals) * 100, 1) if vals else 0)
        matrix.append(row)

    fig = go.Figure(go.Heatmap(
        z=matrix,
        x=nombres_s,
        y=regiones,
        colorscale=[
            [0.0,  "#DC3545"],
            [0.31, "#FD7E14"],
            [0.56, "#2196F3"],
            [0.76, "#20C997"],
            [1.0,  "#7B2FBE"],
        ],
        zmin=0, zmax=100,
        text=[[f"{v:.0f}%" for v in row] for row in matrix],
        texttemplate="%{text}",
        hovertemplate="<b>%{y} — %{x}</b><br>Promedio: %{z:.1f}%<extra></extra>",
        colorbar=dict(title="Puntaje %"),
    ))
    fig.update_layout(
        xaxis=dict(title=""),
        yaxis=dict(title=""),
    )
    return _layout_base(fig, height=350)


def scatter_dispersion(df: pd.DataFrame, eje_x: str = "score_total") -> go.Figure:
    """Build a municipality dispersion chart by score and relative position.

    Args:
        df: Ranking data with score, level, and position columns.
        eje_x: Compatibility argument retained by callers; the chart uses the
            total score percentage.

    Returns:
        Plotly scatter chart.
    """

    df = df.copy()
    df["puntaje_pct"] = df["score_total"] * 100
    df["posicion_inv"] = max(df["posicion"]) - df["posicion"] + 1

    fig = px.scatter(
        df,
        x="puntaje_pct",
        y="posicion_inv",
        color="nivel",
        color_discrete_map=COLORES_NIVEL,
        hover_name="municipalidad",
        hover_data={"puntaje_pct": ":.1f", "nivel": True, "posicion": True, "posicion_inv": False},
        category_orders={"nivel": ORDEN_NIVELES},
        size_max=10,
    )
    fig.update_traces(marker=dict(size=8, opacity=0.8))
    fig.update_layout(
        xaxis=dict(title="Puntaje IGSM (%)", range=[0, 100]),
        yaxis=dict(title="Posición relativa", showticklabels=False),
        legend=dict(title="Nivel"),
    )
    return _layout_base(fig, height=350)


def barras_etapas(etapas: dict) -> go.Figure:
    """Build a bar chart for stage scores.

    Args:
        etapas: Mapping from stage name to score in the 0-1 range.

    Returns:
        Plotly bar chart with stage percentages.
    """

    nombres = list(etapas.keys())
    valores = [v * 100 for v in etapas.values()]
    colores = [COLOR_PRIMARY, COLOR_ACCENT, "#20C997"][:len(nombres)]

    fig = go.Figure(go.Bar(
        x=nombres, y=valores,
        marker_color=colores,
        text=[f"{v:.1f}%" for v in valores],
        textposition="outside",
    ))
    fig.update_layout(
        yaxis=dict(range=[0, 115], title="Puntaje (%)"),
        xaxis=dict(title=""),
        showlegend=False,
    )
    return _layout_base(fig, height=260)


def cluster_chart(df: pd.DataFrame) -> go.Figure:
    """Build a municipality cluster chart.

    Args:
        df: Ranking data with at least total score, region, level, and
            municipality columns.

    Returns:
        Plotly scatter chart with inferred or fallback cluster labels.
    """

    try:
        from sklearn.cluster import KMeans
        import numpy as np
        features = ["score_total"]
        X = df[features].values
        n_clusters = 4
        km = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        df = df.copy()
        df["cluster"] = km.fit_predict(X).astype(str)
    except Exception:
        df = df.copy()
        df["cluster"] = df["nivel"]

    df["puntaje_pct"] = df["score_total"] * 100

    fig = px.scatter(
        df,
        x="puntaje_pct",
        y="region",
        color="cluster",
        hover_name="municipalidad",
        hover_data={"puntaje_pct": ":.1f", "nivel": True},
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    fig.update_traces(marker=dict(size=9, opacity=0.85))
    fig.update_layout(
        xaxis=dict(title="Puntaje IGSM (%)", range=[0, 100]),
        yaxis=dict(title="Región"),
        legend=dict(title="Grupo"),
    )
    return _layout_base(fig, height=380)


def _nivel_por_score(score: float) -> str:
    """Classify a numeric IGSM score into a maturity level.

    Args:
        score: IGSM score in the 0-1 range.

    Returns:
        Maturity level label.
    """

    from data.indicators import clasificar_nivel
    return clasificar_nivel(score)
