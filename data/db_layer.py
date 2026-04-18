# data/db_layer.py — Capa de integración entre SIGAM y la base de datos ORM
# Traduce las llamadas del repositorio al formato que esperan las vistas.

from __future__ import annotations

import os
from datetime import date, datetime
from pathlib import Path

# ── Configurar DATABASE_URL automáticamente si no está definido ──────────────
_DB_PATH = Path(__file__).resolve().parent.parent / "database" / "igsm_dev.sqlite3"
if "DATABASE_URL" not in os.environ:
    os.environ["DATABASE_URL"] = f"sqlite:///{_DB_PATH.as_posix()}"

from database.repositories import (
    list_municipalities,
    get_municipality_by_name,
    get_municipality_by_code,
    get_latest_responses_for_municipality,
    submit_indicator_responses,
    get_latest_stage_weights,
    save_stage_weights,
    get_national_statistics,
)
from data.calculation import calcular_igsm_municipalidad, calcular_consistencia
from data.indicators import clasificar_nivel, COLORES_NIVEL


# ── Helpers internos ─────────────────────────────────────────────────────────

def _build_muni_record(muni: dict, end_date=None, posicion: int = 0) -> dict:
    """Construye el registro completo de una municipalidad con puntaje calculado."""
    codigo = muni["codigo"]
    diversificados = muni.get("diversificados", [])

    respuestas = get_latest_responses_for_municipality(codigo, end_date=end_date)

    try:
        calc = calcular_igsm_municipalidad(respuestas, diversificados)
        score = calc["score_total"]
        nivel = calc["nivel"]
        etapas = calc.get("etapas_scores", {"Planificación": 0.0, "Ejecución": 0.0, "Evaluación": 0.0})
        servicios_scores = {k: v["score"] for k, v in calc["servicios"].items()}
    except Exception:
        score = 0.0
        nivel = "Inicial"
        etapas = {"Planificación": 0.0, "Ejecución": 0.0, "Evaluación": 0.0}
        servicios_scores = {}

    return {
        "codigo":         codigo,
        "municipalidad":  muni["nombre"],
        "provincia":      muni.get("provincia", ""),
        "region":         muni.get("region", ""),
        "lat":            muni.get("lat"),
        "lon":            muni.get("lon"),
        "score_total":    round(score, 4),
        "puntaje_pct":    round(score * 100, 2),
        "nivel":          nivel,
        "etapas":         etapas,
        "servicios":      servicios_scores,
        "posicion":       posicion,
        "estado_envio":   "Enviado" if respuestas else "Pendiente",
        "n_respuestas":   len(respuestas),
    }


# ── API pública ──────────────────────────────────────────────────────────────

def get_ranking(end_date=None) -> list[dict]:
    """Retorna el ranking de las 84 municipalidades con puntajes calculados desde la BD."""
    municipalidades = list_municipalities()
    registros = []
    for muni in municipalidades:
        rec = _build_muni_record(muni, end_date=end_date)
        registros.append(rec)

    registros.sort(key=lambda x: x["score_total"], reverse=True)
    for i, rec in enumerate(registros):
        rec["posicion"] = i + 1

    return registros


def get_municipalidad_data(nombre: str, end_date=None) -> dict | None:
    """Retorna datos completos de una municipalidad por nombre."""
    muni = get_municipality_by_name(nombre)
    if muni is None:
        return None
    return _build_muni_record(muni, end_date=end_date)


def get_municipalidad_data_by_codigo(codigo: str, end_date=None) -> dict | None:
    """Retorna datos completos de una municipalidad por código."""
    muni = get_municipality_by_code(codigo)
    if muni is None:
        return None
    return _build_muni_record(muni, end_date=end_date)


def get_estadisticas_nacionales(end_date=None) -> dict:
    """Retorna KPIs nacionales calculados desde la BD."""
    ranking = get_ranking(end_date=end_date)
    total = len(ranking)
    enviados = sum(1 for m in ranking if m["estado_envio"] == "Enviado")
    scores = [m["score_total"] for m in ranking]
    niveles: dict[str, int] = {}
    for m in ranking:
        n = m["nivel"]
        niveles[n] = niveles.get(n, 0) + 1

    return {
        "total_municipalidades": total,
        "enviados":              enviados,
        "pendientes":            total - enviados,
        "pct_participacion":     round(enviados / total * 100, 1) if total else 0,
        "promedio_nacional":     round(sum(scores) / len(scores), 4) if scores else 0,
        "max_score":             max(scores) if scores else 0,
        "min_score":             min(scores) if scores else 0,
        "distribucion_niveles":  niveles,
    }


def get_scores_por_servicio_nacional(end_date=None) -> dict[str, float]:
    """Retorna el promedio nacional de puntaje por servicio."""
    ranking = get_ranking(end_date=end_date)
    acumulado: dict[str, list[float]] = {}
    for muni in ranking:
        for serv, score in muni["servicios"].items():
            acumulado.setdefault(serv, []).append(score)
    return {serv: round(sum(vals) / len(vals), 4) for serv, vals in acumulado.items() if vals}


def save_responses(municipalidad_codigo: str, respuestas: dict, end_date=None) -> dict:
    """Persiste las respuestas del formulario en la BD."""
    if end_date is None:
        end_date = date.today().isoformat()
    # Filtrar solo respuestas numéricas de indicadores (excluir evidencias "_ev")
    respuestas_limpias = {k: v for k, v in respuestas.items() if not k.endswith("_ev")}
    return submit_indicator_responses(
        municipality_code=municipalidad_codigo,
        end_date=end_date,
        responses=respuestas_limpias,
    )


def load_responses(municipalidad_codigo: str, end_date=None) -> dict:
    """Carga las respuestas más recientes de una municipalidad desde la BD."""
    return get_latest_responses_for_municipality(municipalidad_codigo, end_date=end_date)


def get_weights(end_date=None) -> dict[str, float]:
    """Retorna los pesos de etapa vigentes."""
    return get_latest_stage_weights(end_date=end_date)


def save_weights(planificacion: float, ejecucion: float, evaluacion: float,
                 effective_from: date | None = None) -> dict:
    """Persiste nuevos pesos de etapa en la BD."""
    if effective_from is None:
        effective_from = date.today()
    return save_stage_weights(
        planning=planificacion,
        execution=ejecucion,
        evaluation=evaluacion,
        effective_from=effective_from,
    )
