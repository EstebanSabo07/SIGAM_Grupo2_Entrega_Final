"""Stage-weight management view for the Contraloria portal."""

from __future__ import annotations

from datetime import date

import pandas as pd
import streamlit as st

from components.ui import alert_box, month_year_selector, page_header
from data.indicators import PESOS_ETAPA
from data.presentation_service import get_national_snapshot_view
from data.snapshot import AUDIENCE_ADMIN
from database.repositories import get_latest_stage_weights, save_stage_weights


def show() -> None:
    """Render the IGSM weight management page."""

    page_header(
        "Gestión de pesos",
        "Consulte pesos efectivos, guarde nuevas versiones y simule impacto usando el snapshot seleccionado.",
        "⚖️",
    )
    snapshot = month_year_selector(AUDIENCE_ADMIN, key_prefix="admin_weights_snapshot")
    try:
        effective_weights = get_latest_stage_weights(snapshot.end_date)
    except Exception:
        effective_weights = dict(PESOS_ETAPA)

    plan = st.slider("Planificación (%)", 20, 70, int(effective_weights["Planificación"] * 100), 5)
    ejec = st.slider("Ejecución (%)", 10, 50, int(effective_weights["Ejecución"] * 100), 5)
    eval_ = st.slider("Evaluación (%)", 10, 40, int(effective_weights["Evaluación"] * 100), 5)
    total = plan + ejec + eval_
    if total != 100:
        alert_box(f"La suma actual es {total}%. Debe ser exactamente 100%.", "danger", "❌")
    justification = st.text_area("Justificación técnica", key="weights_justification")

    if st.button("💾 Guardar nueva versión", type="primary", disabled=total != 100):
        if not justification.strip():
            st.error("Debe ingresar una justificación técnica.")
        else:
            save_stage_weights(plan / 100, ejec / 100, eval_ / 100, effective_from=date.today())
            st.success("Pesos guardados correctamente.")

    st.markdown("---")
    st.markdown("##### Simulación de impacto")
    national = get_national_snapshot_view(snapshot, AUDIENCE_ADMIN)
    rows = []
    for municipality in national["municipalities"]:
        stage_scores = municipality["stage_scores"]
        simulated = (
            stage_scores.get("Planificación", 0) * (plan / 100)
            + stage_scores.get("Ejecución", 0) * (ejec / 100)
            + stage_scores.get("Evaluación", 0) * (eval_ / 100)
        )
        rows.append(
            {
                "Municipalidad": municipality["municipality"]["nombre"],
                "Puntaje actual (%)": municipality["puntaje_pct"],
                "Puntaje simulado (%)": round(simulated * 100, 2),
                "Posición actual": municipality["position"],
            }
        )
    simulated_df = pd.DataFrame(rows).sort_values("Puntaje simulado (%)", ascending=False).reset_index(drop=True)
    simulated_df["Posición simulada"] = simulated_df.index + 1
    simulated_df["Variación"] = simulated_df["Posición actual"] - simulated_df["Posición simulada"]
    st.dataframe(simulated_df.head(20), width="stretch", hide_index=True)
