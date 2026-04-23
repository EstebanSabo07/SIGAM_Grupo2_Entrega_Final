"""Mock IGSM data used by legacy and fallback view flows."""

# data/mock_data.py — Datos simulados basados en resultados reales IGSM 2025
# Distribución real 2025: 7 Inicial (8%), 57 Básico (68%), 20 Intermedio (24%)

import random
from data.municipalities import MUNICIPALIDADES
from data.indicators import clasificar_nivel

random.seed(42)

def _score_en_rango(nivel_objetivo: str) -> float:
    """Generate a random score inside a maturity-level range.

    Args:
        nivel_objetivo: Target maturity level.

    Returns:
        Random score in the 0-1 range.
    """

    rangos = {
        "Inicial":     (0.05, 0.30),
        "Básico":      (0.31, 0.55),
        "Intermedio":  (0.56, 0.75),
        "Avanzado":    (0.76, 0.90),
        "Optimizando": (0.91, 0.99),
    }
    lo, hi = rangos[nivel_objetivo]
    return round(random.uniform(lo, hi), 4)

# Asignar niveles siguiendo distribución real 2025 (84 municipalidades)
_DISTRIBUCION = (
    ["Inicial"] * 7 +
    ["Básico"]  * 57 +
    ["Intermedio"] * 20
)
random.shuffle(_DISTRIBUCION)

# Scores por servicio (base nacional real del informe 2025)
_SCORES_SERVICIO_BASE = {
    "Recolección, depósito y tratamiento de residuos sólidos": 0.48,
    "Aseo de vías y sitios públicos":                          0.32,
    "Urbanismo e infraestructura":                             0.42,
    "Red vial cantonal":                                       0.40,
    "Servicios sociales y complementarios":                    0.55,
    "Servicios educativos, culturales y deportivos":           0.51,
    "Alcantarillado pluvial":                                  0.28,
    "Agua potable":                                            0.44,
    "Zona Marítimo Terrestre":                                 0.45,
    "Seguridad y vigilancia":                                  0.38,
}

def _generar_score_servicio(base: float, variacion: float = 0.15) -> float:
    """Generate a bounded service score around a base value.

    Args:
        base: Base score in the 0-1 range.
        variacion: Maximum random variation applied in either direction.

    Returns:
        Service score clipped to the 0-1 range.
    """

    return round(max(0, min(1, base + random.uniform(-variacion, variacion))), 4)

def _generar_historial(score_actual: float) -> list:
    """Generate a plausible 2022-2024 score history.

    Args:
        score_actual: Current score used as the trend anchor.

    Returns:
        Three historical scores ordered from 2022 to 2024.
    """

    hist = []
    s = score_actual + random.uniform(-0.12, -0.02)
    for _ in range(3):
        s = max(0.05, min(0.99, s + random.uniform(-0.03, 0.05)))
        hist.append(round(s, 4))
    return hist  # [2022, 2023, 2024]

# ── Generar datos de todas las municipalidades ────────────────────────────────
MOCK_RANKING = []

for i, muni in enumerate(MUNICIPALIDADES):
    nivel_obj = _DISTRIBUCION[i]
    score = _score_en_rango(nivel_obj)
    nivel = clasificar_nivel(score)

    # Scores por servicio
    servicios_scores = {}
    for serv, base in _SCORES_SERVICIO_BASE.items():
        # Ajustar base según score global
        factor = score / 0.45  # normalizar alrededor del promedio
        servicios_scores[serv] = _generar_score_servicio(base * factor)

    # Scores por etapa (globales)
    plan_base = score * 1.05
    ejec_base = score * 0.95
    eval_base = score * 0.85
    etapas = {
        "Planificación": round(min(1, plan_base + random.uniform(-0.05, 0.05)), 4),
        "Ejecución":     round(min(1, ejec_base + random.uniform(-0.05, 0.05)), 4),
        "Evaluación":    round(min(1, eval_base + random.uniform(-0.08, 0.05)), 4),
    }

    historial = _generar_historial(score)

    MOCK_RANKING.append({
        "codigo":      muni["codigo"],
        "municipalidad": muni["nombre"],
        "provincia":   muni["provincia"],
        "region":      muni["region"],
        "lat":         muni["lat"],
        "lon":         muni["lon"],
        "score_total": score,
        "puntaje_pct": round(score * 100, 2),
        "nivel":       nivel,
        "etapas":      etapas,
        "servicios":   servicios_scores,
        "historial":   historial,  # [2022, 2023, 2024]
        "periodo":     "2025",
        "estado_envio": random.choice(["Enviado", "Enviado", "Enviado", "Pendiente"]),
    })

# Ordenar por score descendente
MOCK_RANKING.sort(key=lambda x: x["score_total"], reverse=True)

# Asignar posición en ranking
for i, m in enumerate(MOCK_RANKING):
    m["posicion"] = i + 1

# ── Funciones de acceso ───────────────────────────────────────────────────────

def get_ranking() -> list:
    """Return the mock national ranking.

    Returns:
        List of mock municipality records ordered by score.
    """

    return MOCK_RANKING

def get_municipalidad_data(nombre: str) -> dict:
    """Return a mock municipality record by name.

    Args:
        nombre: Municipality display name.

    Returns:
        Matching municipality record, or None when not found.
    """

    for m in MOCK_RANKING:
        if m["municipalidad"] == nombre:
            return m
    return None

def get_municipalidad_by_codigo(codigo: str) -> dict:
    """Return a mock municipality record by code.

    Args:
        codigo: Municipality code.

    Returns:
        Matching municipality record, or None when not found.
    """

    for m in MOCK_RANKING:
        if m["codigo"] == codigo:
            return m
    return None

def get_estadisticas_nacionales() -> dict:
    """Return national statistics calculated from mock data.

    Returns:
        Mock national totals, participation metrics, score extrema, and level
        distribution.
    """

    total = len(MOCK_RANKING)
    enviados = sum(1 for m in MOCK_RANKING if m["estado_envio"] == "Enviado")
    scores = [m["score_total"] for m in MOCK_RANKING]
    niveles = {}
    for m in MOCK_RANKING:
        n = m["nivel"]
        niveles[n] = niveles.get(n, 0) + 1

    return {
        "total_municipalidades": total,
        "enviados": enviados,
        "pendientes": total - enviados,
        "pct_participacion": round(enviados / total * 100, 1),
        "promedio_nacional": round(sum(scores) / len(scores), 4),
        "max_score": max(scores),
        "min_score": min(scores),
        "distribucion_niveles": niveles,
    }

def get_historial_nacional() -> dict:
    """Return mock national historical data for 2022-2025.

    Returns:
        Mapping from year to average score and maturity-level counts.
    """

    return {
        "2022": {"promedio": 0.37, "Inicial": 12, "Básico": 58, "Intermedio": 14, "Avanzado": 0, "Optimizando": 0},
        "2023": {"promedio": 0.39, "Inicial": 10, "Básico": 56, "Intermedio": 16, "Avanzado": 0, "Optimizando": 0},
        "2024": {"promedio": 0.41, "Inicial": 9,  "Básico": 57, "Intermedio": 18, "Avanzado": 0, "Optimizando": 0},
        "2025": {"promedio": 0.43, "Inicial": 7,  "Básico": 57, "Intermedio": 20, "Avanzado": 0, "Optimizando": 0},
    }

def get_scores_por_servicio_nacional() -> dict:
    """Return mock national average scores by service.

    Returns:
        Mapping from service name to average score.
    """

    promedios = {}
    for serv in _SCORES_SERVICIO_BASE:
        vals = [m["servicios"].get(serv, 0) for m in MOCK_RANKING if serv in m["servicios"]]
        if vals:
            promedios[serv] = round(sum(vals) / len(vals), 4)
    return promedios
