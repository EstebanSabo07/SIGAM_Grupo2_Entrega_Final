# data/calculation.py — Motor de cálculo IGSM (replicación exacta de la metodología CGR)
# Fuente: igsm_replicacion_IGSM2025-actualizado_grupo2.ipynb (97.6% → 100% exactitud con ajuste)

from data.indicators import ESTRUCTURA_IGSM, UMBRALES_NIVEL, TIPO_INFORMATIVO, PESOS_ETAPA

def clasificar_nivel(score: float) -> str:
    """Clasifica un score en su nivel de madurez oficial."""
    for lo, hi, nivel in UMBRALES_NIVEL:
        if lo <= score < hi:
            return nivel
    return "Optimizando"

def calcular_score_servicio(respuestas: dict, servicio_nombre: str, eje_nombre: str) -> dict:
    """
    Calcula el puntaje de un servicio para una municipalidad.

    Fórmula por etapa:
        score_etapa = Σ(valores_indicadores) / n_indicadores_en_etapa
    Score final del servicio:
        score = Σ_etapas (peso_etapa × score_etapa)
    """
    serv_data = ESTRUCTURA_IGSM[eje_nombre]["servicios"][servicio_nombre]
    resultado = {"servicio": servicio_nombre, "eje": eje_nombre, "etapas": {}, "score": 0.0}

    score_total = 0.0
    for etapa, peso in PESOS_ETAPA.items():
        indicadores = [
            ind for ind in serv_data["etapas"].get(etapa, [])
            if ind["tipo"] != TIPO_INFORMATIVO
        ]
        n = len(indicadores)
        if n == 0:
            resultado["etapas"][etapa] = {"score": 0.0, "n": 0, "cumplidos": 0}
            continue

        cumplidos = 0
        for ind in indicadores:
            val = respuestas.get(ind["codigo"], 0)
            if isinstance(val, bool):
                val = 1.0 if val else 0.0
            cumplidos += float(val)

        score_etapa = cumplidos / n
        score_total += peso * score_etapa
        resultado["etapas"][etapa] = {
            "score": round(score_etapa, 4),
            "n": n,
            "cumplidos": cumplidos,
        }

    resultado["score"] = round(score_total, 4)
    return resultado


def calcular_igsm_municipalidad(respuestas: dict, diversificados: list) -> dict:
    """
    Calcula el IGSM total de una municipalidad.

    Metodología CGR:
    1. Solo se incluyen servicios donde la municipalidad tiene al menos una respuesta
    2. Pesos por indicador = peso_etapa / n_total_indicadores_en_etapa (solo servicios con respuestas)
    3. Score = Σ(valor_ind × peso_ind)

    Retorna dict con score_total, nivel, detalle por servicio y etapa.
    """
    from data.indicators import get_servicios_para_municipalidad

    servicios_candidatos = get_servicios_para_municipalidad(diversificados)

    # Solo incluir servicios donde la municipalidad tiene al menos una respuesta
    codigos_respondidos = set(respuestas.keys())
    servicios_aplicables = {}
    for serv_nombre, serv_data in servicios_candidatos.items():
        eje_nombre = serv_data["eje"]
        codigos_serv = set()
        for etapa_inds in ESTRUCTURA_IGSM[eje_nombre]["servicios"][serv_nombre]["etapas"].values():
            for ind in etapa_inds:
                if ind["tipo"] != TIPO_INFORMATIVO:
                    codigos_serv.add(ind["codigo"])
        if codigos_serv & codigos_respondidos:  # tiene al menos una respuesta
            servicios_aplicables[serv_nombre] = serv_data

    # Contar indicadores totales por etapa (para calcular pesos globales)
    n_por_etapa = {"Planificación": 0, "Ejecución": 0, "Evaluación": 0}
    for serv_nombre, serv_data in servicios_aplicables.items():
        eje_nombre = serv_data["eje"]
        for etapa in PESOS_ETAPA:
            inds = ESTRUCTURA_IGSM[eje_nombre]["servicios"][serv_nombre]["etapas"].get(etapa, [])
            n_por_etapa[etapa] += len([i for i in inds if i["tipo"] != TIPO_INFORMATIVO])

    # Pesos globales por indicador
    pesos_por_ind = {}
    for etapa, peso_etapa in PESOS_ETAPA.items():
        n = n_por_etapa[etapa]
        if n > 0:
            pesos_por_ind[etapa] = peso_etapa / n

    # Calcular score total
    score_total = 0.0
    detalle_servicios = {}

    for serv_nombre, serv_data in servicios_aplicables.items():
        eje_nombre = serv_data["eje"]
        serv_score = 0.0
        serv_detalle = {"eje": eje_nombre, "etapas": {}}

        for etapa in PESOS_ETAPA:
            inds = ESTRUCTURA_IGSM[eje_nombre]["servicios"][serv_nombre]["etapas"].get(etapa, [])
            inds_scored = [i for i in inds if i["tipo"] != TIPO_INFORMATIVO]

            cumplidos = 0
            for ind in inds_scored:
                val = respuestas.get(ind["codigo"], 0)
                if isinstance(val, bool):
                    val = 1.0 if val else 0.0
                peso_ind = pesos_por_ind.get(etapa, 0)
                contrib = float(val) * peso_ind
                score_total += contrib
                serv_score += contrib
                cumplidos += float(val)

            n = len(inds_scored)
            serv_detalle["etapas"][etapa] = {
                "n": n,
                "cumplidos": cumplidos,
                "score": round(cumplidos / n, 4) if n > 0 else 0.0,
            }

        serv_detalle["score"] = round(serv_score, 4)
        detalle_servicios[serv_nombre] = serv_detalle

    score_total = round(score_total, 4)
    nivel = clasificar_nivel(score_total)

    return {
        "score_total": score_total,
        "nivel": nivel,
        "puntaje_porcentaje": round(score_total * 100, 2),
        "servicios": detalle_servicios,
        "n_servicios": len(servicios_aplicables),
        "n_indicadores": sum(n_por_etapa.values()),
    }


def calcular_consistencia(respuestas: dict, diversificados: list) -> dict:
    """
    Índice de consistencia interna: detecta inconsistencias lógicas en las respuestas.
    Retorna lista de inconsistencias encontradas.
    """
    inconsistencias = []

    # Regla 1: No puede tener plan sin brindar el servicio
    # 1.1.1.1 = Se brinda el servicio | 1.1.1.3 = Plan municipal de gestión integral
    servicio_brindado = respuestas.get("1.1.1.1", 0)
    tiene_plan = respuestas.get("1.1.1.3", 0)
    if not servicio_brindado and tiene_plan:
        inconsistencias.append({
            "tipo": "Lógica",
            "descripcion": "Se declara Plan de Gestión de Residuos pero no se brinda el servicio (1.1.1.1 = No, 1.1.1.3 = Sí)",
            "severidad": "Alta",
        })

    # Regla 2: No puede tener plan de mejora sin evaluación previa
    # 1.1.1.24 = Evaluación de la calidad | 1.1.1.25 = Plan de mejora
    tiene_eval = respuestas.get("1.1.1.24", 0)
    tiene_plan_mejora = respuestas.get("1.1.1.25", 0)
    if not tiene_eval and tiene_plan_mejora:
        inconsistencias.append({
            "tipo": "Secuencia",
            "descripcion": "Plan de mejora declarado sin haber realizado evaluación del servicio (1.1.1.24 = No, 1.1.1.25 = Sí)",
            "severidad": "Media",
        })

    # Regla 3: No puede haber plan de mejora sin brindar el servicio
    if tiene_plan_mejora and not servicio_brindado:
        inconsistencias.append({
            "tipo": "Secuencia",
            "descripcion": "Se declara Plan de mejora del servicio pero no se brinda el servicio (1.1.1.1 = No, 1.1.1.25 = Sí)",
            "severidad": "Alta",
        })

    score_consistencia = max(0, 1.0 - (len(inconsistencias) * 0.2))
    return {
        "inconsistencias": inconsistencias,
        "n_inconsistencias": len(inconsistencias),
        "score_consistencia": round(score_consistencia, 2),
        "estado": "Consistente" if len(inconsistencias) == 0 else
                  "Alerta" if len(inconsistencias) <= 2 else "Crítico",
    }


def detectar_anomalia_historica(score_actual: float, historial: list) -> dict:
    """
    Detecta si el score actual es una anomalía respecto al historial.
    historial: lista de scores anteriores [score_2023, score_2024, ...]
    """
    if len(historial) < 1:
        return {"es_anomalia": False, "mensaje": "Sin historial suficiente"}

    promedio = sum(historial) / len(historial)
    ultimo = historial[-1]
    variacion = score_actual - ultimo
    variacion_pct = (variacion / ultimo * 100) if ultimo > 0 else 0

    umbral_sospecha = 0.15  # 15% de variación es sospechoso

    es_anomalia = abs(variacion) > umbral_sospecha
    return {
        "es_anomalia": es_anomalia,
        "variacion": round(variacion, 4),
        "variacion_pct": round(variacion_pct, 2),
        "promedio_historico": round(promedio, 4),
        "mensaje": (
            f"⚠️ Variación inusual: +{variacion_pct:.1f}% respecto al período anterior"
            if es_anomalia and variacion > 0
            else f"⚠️ Caída inusual: {variacion_pct:.1f}% respecto al período anterior"
            if es_anomalia
            else "✅ Variación dentro de parámetros normales"
        ),
    }
