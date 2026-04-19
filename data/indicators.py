"""Static IGSM indicator structure and maturity helpers."""

# data/indicators.py — Estructura completa del IGSM 2025 (159 indicadores)
# Fuente: PT-228 Contraloría General de la República de Costa Rica (2025)
# Estructura oficial: 10 servicios, 3 ejes, 159 indicadores puntuables

# Tipos de indicador
TIPO_BINARIO    = "binario"      # Sí / No → puntaje 0 o 1
TIPO_COBERTURA  = "cobertura"    # Fórmula de cobertura por distrito (0, 0.25, 0.50, 1)
TIPO_PORCENTAJE = "porcentaje"   # Valor numérico con fórmula (0 a 1)
TIPO_INFORMATIVO= "informativo"  # No tiene puntaje, solo informativo
TIPO_DECISION   = "decision"     # Bifurca hacia otros indicadores

# Etapas y sus pesos globales (metodología CGR)
PESOS_ETAPA = {
    "Planificación": 0.50,
    "Ejecución":     0.30,
    "Evaluación":    0.20,
}

# Umbrales oficiales de nivel de madurez (CGR PT-228 2025)
UMBRALES_NIVEL = [
    (0.00, 0.31, "Inicial"),
    (0.31, 0.56, "Básico"),
    (0.56, 0.76, "Intermedio"),
    (0.76, 0.91, "Avanzado"),
    (0.91, 1.01, "Optimizando"),
]

COLORES_NIVEL = {
    "Inicial":     "#DC3545",
    "Básico":      "#FD7E14",
    "Intermedio":  "#2196F3",
    "Avanzado":    "#20C997",
    "Optimizando": "#7B2FBE",
}

def clasificar_nivel(score: float) -> str:
    """Classify an IGSM score into a maturity level.

    Args:
        score: IGSM score in the 0-1 range.

    Returns:
        Maturity level label.
    """

    for lo, hi, nivel in UMBRALES_NIVEL:
        if lo <= score < hi:
            return nivel
    return "Optimizando"

# ── Estructura de servicios e indicadores ────────────────────────────────────
# Organización: Eje → Servicio → Etapa → Indicadores
# Códigos según PT-228 CGR 2025:
#   1.1.x = Salubridad Pública (básico)
#   1.2.x = Desarrollo Urbano (básico)
#   1.3.x = Servicios Sociales (básico)
#   2.x.x = Servicios especializados (diversificados)

ESTRUCTURA_IGSM = {

    # ═══════════════════════════════════════════════════════════════════════
    # EJE 1.1 — SALUBRIDAD PÚBLICA (servicios básicos)
    # ═══════════════════════════════════════════════════════════════════════
    "Salubridad Pública": {
        "tipo": "eje",
        "codigo": "1.1",
        "servicios": {

            # ─── Servicio 1.1.1 — Recolección, depósito y tratamiento de residuos sólidos ───
            # Planificación: 9  |  Ejecución: 14  |  Evaluación: 2  |  TOTAL: 25
            "Recolección, depósito y tratamiento de residuos sólidos": {
                "codigo_servicio": "1.1.1",
                "agrupacion": "Básico",
                "etapas": {
                    "Planificación": [
                        {"codigo": "1.1.1.1",  "nombre": "Se brinda el servicio de recolección, depósito y tratamiento de residuos", "tipo": TIPO_BINARIO, "evidencia": False},
                        {"codigo": "1.1.1.2",  "nombre": "Reglamento del servicio de recolección y tratamiento de residuos", "tipo": TIPO_BINARIO, "evidencia": True, "doc": "Reglamento vigente del servicio"},
                        {"codigo": "1.1.1.3",  "nombre": "Plan municipal de gestión integral de residuos sólidos", "tipo": TIPO_BINARIO, "evidencia": True, "doc": "Plan de gestión integral de residuos vigente"},
                        {"codigo": "1.1.1.4",  "nombre": "Identificación de la población vulnerable para la prestación del servicio", "tipo": TIPO_BINARIO, "evidencia": False},
                        {"codigo": "1.1.1.5",  "nombre": "Inclusión de la población vulnerable en la planificación del servicio", "tipo": TIPO_BINARIO, "evidencia": False},
                        {"codigo": "1.1.1.6",  "nombre": "Actualización de la tasa por el servicio de recolección de residuos", "tipo": TIPO_BINARIO, "evidencia": True, "doc": "Publicación vigente en La Gaceta"},
                        {"codigo": "1.1.1.7",  "nombre": "Estrategias de promoción de la gestión integral de residuos en la ciudadanía", "tipo": TIPO_BINARIO, "evidencia": False},
                        {"codigo": "1.1.1.8",  "nombre": "Existencia de una unidad de gestión ambiental municipal", "tipo": TIPO_BINARIO, "evidencia": False},
                        {"codigo": "1.1.1.9",  "nombre": "Centro municipal de recuperación de residuos valorizables", "tipo": TIPO_BINARIO, "evidencia": False},
                    ],
                    "Ejecución": [
                        {"codigo": "1.1.1.10", "nombre": "Cobertura del servicio de recolección de residuos sólidos", "tipo": TIPO_COBERTURA, "evidencia": False},
                        {"codigo": "1.1.1.11", "nombre": "Recolección diferenciada de residuos valorizables", "tipo": TIPO_BINARIO, "evidencia": False},
                        {"codigo": "1.1.1.12", "nombre": "Cobertura del servicio de recolección de residuos valorizables", "tipo": TIPO_COBERTURA, "evidencia": False},
                        {"codigo": "1.1.1.13", "nombre": "Porcentaje de valorización en el servicio de recolección de residuos", "tipo": TIPO_PORCENTAJE, "evidencia": False},
                        {"codigo": "1.1.1.14", "nombre": "Sensibilización ciudadana en materia de gestión de residuos", "tipo": TIPO_BINARIO, "evidencia": False},
                        {"codigo": "1.1.1.15", "nombre": "Nivel de ejecución de los recursos disponibles del servicio", "tipo": TIPO_PORCENTAJE, "evidencia": False},
                        {"codigo": "1.1.1.16", "nombre": "Recursos del servicio destinados por distrito", "tipo": TIPO_PORCENTAJE, "evidencia": False},
                        {"codigo": "1.1.1.17", "nombre": "Morosidad del servicio de recolección de residuos", "tipo": TIPO_PORCENTAJE, "evidencia": False},
                        {"codigo": "1.1.1.18", "nombre": "Gestión de residuos especiales o peligrosos", "tipo": TIPO_BINARIO, "evidencia": False},
                        {"codigo": "1.1.1.19", "nombre": "Disposición final ambientalmente adecuada de residuos sólidos", "tipo": TIPO_BINARIO, "evidencia": True, "doc": "Contrato o convenio con sitio de disposición final"},
                        {"codigo": "1.1.1.20", "nombre": "Accesibilidad del servicio para personas con discapacidad", "tipo": TIPO_BINARIO, "evidencia": False},
                        {"codigo": "1.1.1.21", "nombre": "Atención de quejas y denuncias sobre el servicio de recolección", "tipo": TIPO_BINARIO, "evidencia": False},
                        {"codigo": "1.1.1.22", "nombre": "Frecuencia establecida y cumplida de recolección por ruta", "tipo": TIPO_BINARIO, "evidencia": False},
                        {"codigo": "1.1.1.23", "nombre": "Programa de compostaje o aprovechamiento de residuos orgánicos", "tipo": TIPO_BINARIO, "evidencia": False},
                    ],
                    "Evaluación": [
                        {"codigo": "1.1.1.24", "nombre": "Evaluación de la calidad del servicio de recolección de residuos sólidos", "tipo": TIPO_BINARIO, "evidencia": True, "doc": "Informe de evaluación del servicio"},
                        {"codigo": "1.1.1.25", "nombre": "Plan de mejora del servicio de recolección de residuos sólidos", "tipo": TIPO_BINARIO, "evidencia": True, "doc": "Plan de mejora vigente con avances"},
                    ],
                },
            },

            # ─── Servicio 1.1.2 — Aseo de vías y sitios públicos ───
            # Planificación: 5  |  Ejecución: 5  |  Evaluación: 2  |  TOTAL: 12
            "Aseo de vías y sitios públicos": {
                "codigo_servicio": "1.1.2",
                "agrupacion": "Básico",
                "etapas": {
                    "Planificación": [
                        {"codigo": "1.1.2.1", "nombre": "Se brinda el servicio de aseo de vías y sitios públicos", "tipo": TIPO_BINARIO, "evidencia": False},
                        {"codigo": "1.1.2.2", "nombre": "Reglamento del servicio de aseo de vías y sitios públicos", "tipo": TIPO_BINARIO, "evidencia": True, "doc": "Reglamento vigente del servicio"},
                        {"codigo": "1.1.2.3", "nombre": "Plan del servicio de aseo de vías y sitios públicos", "tipo": TIPO_BINARIO, "evidencia": True, "doc": "Plan operativo o de gestión del servicio"},
                        {"codigo": "1.1.2.4", "nombre": "Identificación de sitios públicos prioritarios para el aseo", "tipo": TIPO_BINARIO, "evidencia": False},
                        {"codigo": "1.1.2.5", "nombre": "Actualización de la tasa del servicio de aseo de vías", "tipo": TIPO_BINARIO, "evidencia": True, "doc": "Publicación vigente en La Gaceta"},
                    ],
                    "Ejecución": [
                        {"codigo": "1.1.2.6",  "nombre": "Cobertura del servicio de aseo de vías y sitios públicos", "tipo": TIPO_COBERTURA, "evidencia": False},
                        {"codigo": "1.1.2.7",  "nombre": "Frecuencia del servicio de aseo de vías", "tipo": TIPO_BINARIO, "evidencia": False},
                        {"codigo": "1.1.2.8",  "nombre": "Nivel de ejecución de los recursos del servicio de aseo de vías", "tipo": TIPO_PORCENTAJE, "evidencia": False},
                        {"codigo": "1.1.2.9",  "nombre": "Recursos destinados al desarrollo del servicio de aseo de vías", "tipo": TIPO_PORCENTAJE, "evidencia": False},
                        {"codigo": "1.1.2.10", "nombre": "Morosidad del servicio de aseo de vías y sitios públicos", "tipo": TIPO_PORCENTAJE, "evidencia": False},
                    ],
                    "Evaluación": [
                        {"codigo": "1.1.2.11", "nombre": "Evaluación de la calidad del servicio de aseo de vías", "tipo": TIPO_BINARIO, "evidencia": False},
                        {"codigo": "1.1.2.12", "nombre": "Plan de mejora del servicio de aseo de vías y sitios públicos", "tipo": TIPO_BINARIO, "evidencia": True, "doc": "Plan de mejora vigente"},
                    ],
                },
            },
        },
    },

    # ═══════════════════════════════════════════════════════════════════════
    # EJE 1.2 — DESARROLLO URBANO (servicios básicos)
    # ═══════════════════════════════════════════════════════════════════════
    "Desarrollo Urbano": {
        "tipo": "eje",
        "codigo": "1.2",
        "servicios": {

            # ─── Servicio 1.2.1 — Urbanismo e infraestructura ───
            # Planificación: 6  |  Ejecución: 2  |  Evaluación: 7  |  TOTAL: 15
            "Urbanismo e infraestructura": {
                "codigo_servicio": "1.2.1",
                "agrupacion": "Básico",
                "etapas": {
                    "Planificación": [
                        {"codigo": "1.2.1.1", "nombre": "Reglamento de desarrollo urbanístico cantonal", "tipo": TIPO_BINARIO, "evidencia": True, "doc": "Reglamento vigente"},
                        {"codigo": "1.2.1.2", "nombre": "Plan regulador cantonal vigente", "tipo": TIPO_BINARIO, "evidencia": True, "doc": "Plan regulador aprobado por INVU"},
                        {"codigo": "1.2.1.3", "nombre": "Plan de ordenamiento territorial cantonal", "tipo": TIPO_BINARIO, "evidencia": True, "doc": "Plan de ordenamiento territorial vigente"},
                        {"codigo": "1.2.1.4", "nombre": "Identificación y mapa de zonas de riesgo cantonal", "tipo": TIPO_BINARIO, "evidencia": True, "doc": "Mapa actualizado de zonas de riesgo"},
                        {"codigo": "1.2.1.5", "nombre": "Inclusión de población vulnerable en la planificación urbana", "tipo": TIPO_BINARIO, "evidencia": False},
                        {"codigo": "1.2.1.6", "nombre": "Sistema de información geográfica cantonal (SIG)", "tipo": TIPO_BINARIO, "evidencia": False},
                    ],
                    "Ejecución": [
                        {"codigo": "1.2.1.7", "nombre": "Nivel de ejecución de los recursos disponibles del servicio", "tipo": TIPO_PORCENTAJE, "evidencia": False},
                        {"codigo": "1.2.1.8", "nombre": "Permisos de construcción tramitados oportunamente", "tipo": TIPO_PORCENTAJE, "evidencia": False},
                    ],
                    "Evaluación": [
                        {"codigo": "1.2.1.9",  "nombre": "Evaluación del plan regulador cantonal", "tipo": TIPO_BINARIO, "evidencia": False},
                        {"codigo": "1.2.1.10", "nombre": "Control y seguimiento de asentamientos informales", "tipo": TIPO_BINARIO, "evidencia": False},
                        {"codigo": "1.2.1.11", "nombre": "Inspecciones urbanísticas realizadas respecto a las programadas", "tipo": TIPO_PORCENTAJE, "evidencia": False},
                        {"codigo": "1.2.1.12", "nombre": "Accesibilidad universal en espacios públicos cantonales", "tipo": TIPO_BINARIO, "evidencia": False},
                        {"codigo": "1.2.1.13", "nombre": "Gestión de riesgos ante desastres naturales", "tipo": TIPO_BINARIO, "evidencia": True, "doc": "Plan de gestión de riesgos"},
                        {"codigo": "1.2.1.14", "nombre": "Plan de mejora del servicio de urbanismo e infraestructura", "tipo": TIPO_BINARIO, "evidencia": True, "doc": "Plan de mejora vigente"},
                        {"codigo": "1.2.1.15", "nombre": "Satisfacción ciudadana con el ordenamiento territorial", "tipo": TIPO_BINARIO, "evidencia": True, "doc": "Estudio de percepción ciudadana"},
                    ],
                },
            },

            # ─── Servicio 1.2.2 — Red vial cantonal ───
            # Planificación: 7  |  Ejecución: 8  |  Evaluación: 5  |  TOTAL: 20
            "Red vial cantonal": {
                "codigo_servicio": "1.2.2",
                "agrupacion": "Básico",
                "etapas": {
                    "Planificación": [
                        {"codigo": "1.2.2.1", "nombre": "Reglamento de la red vial cantonal", "tipo": TIPO_BINARIO, "evidencia": True, "doc": "Reglamento vigente de gestión vial"},
                        {"codigo": "1.2.2.2", "nombre": "Plan de conservación vial cantonal", "tipo": TIPO_BINARIO, "evidencia": True, "doc": "Plan de conservación vial vigente"},
                        {"codigo": "1.2.2.3", "nombre": "Inventario vial cantonal actualizado", "tipo": TIPO_BINARIO, "evidencia": True, "doc": "Inventario vial actualizado (máx. 2 años)"},
                        {"codigo": "1.2.2.4", "nombre": "Diagnóstico del estado de la red vial cantonal", "tipo": TIPO_BINARIO, "evidencia": True, "doc": "Informe diagnóstico técnico de la red vial"},
                        {"codigo": "1.2.2.5", "nombre": "Identificación de necesidades viales de la población vulnerable", "tipo": TIPO_BINARIO, "evidencia": False},
                        {"codigo": "1.2.2.6", "nombre": "Presupuesto anual destinado al mantenimiento vial cantonal", "tipo": TIPO_PORCENTAJE, "evidencia": False},
                        {"codigo": "1.2.2.7", "nombre": "Coordinación con MOPT y CONAVI para intervenciones viales", "tipo": TIPO_BINARIO, "evidencia": False},
                    ],
                    "Ejecución": [
                        {"codigo": "1.2.2.8",  "nombre": "Mantenimiento rutinario de la red vial cantonal", "tipo": TIPO_BINARIO, "evidencia": False},
                        {"codigo": "1.2.2.9",  "nombre": "Mantenimiento periódico de la red vial cantonal", "tipo": TIPO_BINARIO, "evidencia": False},
                        {"codigo": "1.2.2.10", "nombre": "Obras de mejoramiento o construcción vial", "tipo": TIPO_BINARIO, "evidencia": False},
                        {"codigo": "1.2.2.11", "nombre": "Señalización horizontal y vertical de la red vial", "tipo": TIPO_BINARIO, "evidencia": False},
                        {"codigo": "1.2.2.12", "nombre": "Nivel de ejecución de los recursos disponibles del servicio vial", "tipo": TIPO_PORCENTAJE, "evidencia": False},
                        {"codigo": "1.2.2.13", "nombre": "Cobertura del servicio de mantenimiento vial por distrito", "tipo": TIPO_COBERTURA, "evidencia": False},
                        {"codigo": "1.2.2.14", "nombre": "Accesibilidad vial para personas con discapacidad", "tipo": TIPO_BINARIO, "evidencia": False},
                        {"codigo": "1.2.2.15", "nombre": "Recursos destinados al servicio vial por distrito", "tipo": TIPO_PORCENTAJE, "evidencia": False},
                    ],
                    "Evaluación": [
                        {"codigo": "1.2.2.16", "nombre": "Evaluación del estado de la red vial cantonal", "tipo": TIPO_BINARIO, "evidencia": True, "doc": "Informe de evaluación del estado vial"},
                        {"codigo": "1.2.2.17", "nombre": "Satisfacción ciudadana con el servicio vial cantonal", "tipo": TIPO_BINARIO, "evidencia": True, "doc": "Estudio de satisfacción del usuario"},
                        {"codigo": "1.2.2.18", "nombre": "Plan de mejora de la red vial cantonal", "tipo": TIPO_BINARIO, "evidencia": True, "doc": "Plan de mejora vial vigente"},
                        {"codigo": "1.2.2.19", "nombre": "Implementación del plan de mejora vial", "tipo": TIPO_BINARIO, "evidencia": False},
                        {"codigo": "1.2.2.20", "nombre": "Inclusión de enfoque de género en la evaluación del servicio vial", "tipo": TIPO_BINARIO, "evidencia": False},
                    ],
                },
            },

            # ─── Servicio 1.2.3 — Alcantarillado pluvial ───
            # Planificación: 7  |  Ejecución: 6  |  Evaluación: 2  |  TOTAL: 15
            "Alcantarillado pluvial": {
                "codigo_servicio": "1.2.3",
                "agrupacion": "Básico",
                "etapas": {
                    "Planificación": [
                        {"codigo": "1.2.3.1", "nombre": "Se brinda el servicio de alcantarillado pluvial", "tipo": TIPO_BINARIO, "evidencia": False},
                        {"codigo": "1.2.3.2", "nombre": "Reglamento del servicio de alcantarillado pluvial", "tipo": TIPO_BINARIO, "evidencia": True, "doc": "Reglamento vigente del servicio"},
                        {"codigo": "1.2.3.3", "nombre": "Plan del servicio de alcantarillado pluvial", "tipo": TIPO_BINARIO, "evidencia": True, "doc": "Plan de gestión del sistema pluvial"},
                        {"codigo": "1.2.3.4", "nombre": "Diagnóstico técnico del sistema de alcantarillado pluvial", "tipo": TIPO_BINARIO, "evidencia": True, "doc": "Diagnóstico técnico del sistema pluvial"},
                        {"codigo": "1.2.3.5", "nombre": "Inventario del sistema de alcantarillado pluvial", "tipo": TIPO_BINARIO, "evidencia": True, "doc": "Inventario actualizado del sistema"},
                        {"codigo": "1.2.3.6", "nombre": "Actualización de la tasa del servicio de alcantarillado pluvial", "tipo": TIPO_BINARIO, "evidencia": True, "doc": "Publicación vigente en La Gaceta"},
                        {"codigo": "1.2.3.7", "nombre": "Identificación de zonas de inundación y riesgo pluvial", "tipo": TIPO_BINARIO, "evidencia": True, "doc": "Mapa de zonas de inundación"},
                    ],
                    "Ejecución": [
                        {"codigo": "1.2.3.8",  "nombre": "Mantenimiento preventivo del sistema de alcantarillado pluvial", "tipo": TIPO_BINARIO, "evidencia": False},
                        {"codigo": "1.2.3.9",  "nombre": "Control e inspección del sistema pluvial", "tipo": TIPO_BINARIO, "evidencia": False},
                        {"codigo": "1.2.3.10", "nombre": "Nivel de ejecución de los recursos disponibles del servicio", "tipo": TIPO_PORCENTAJE, "evidencia": False},
                        {"codigo": "1.2.3.11", "nombre": "Recursos destinados al desarrollo del servicio de alcantarillado", "tipo": TIPO_PORCENTAJE, "evidencia": False},
                        {"codigo": "1.2.3.12", "nombre": "Morosidad del servicio de alcantarillado pluvial", "tipo": TIPO_PORCENTAJE, "evidencia": False},
                        {"codigo": "1.2.3.13", "nombre": "Detección y control de vertidos inadecuados al sistema pluvial", "tipo": TIPO_BINARIO, "evidencia": False},
                    ],
                    "Evaluación": [
                        {"codigo": "1.2.3.14", "nombre": "Evaluación de la calidad y eficiencia del sistema pluvial", "tipo": TIPO_BINARIO, "evidencia": False},
                        {"codigo": "1.2.3.15", "nombre": "Plan de mejora del servicio de alcantarillado pluvial", "tipo": TIPO_BINARIO, "evidencia": True, "doc": "Plan de mejora vigente"},
                    ],
                },
            },
        },
    },

    # ═══════════════════════════════════════════════════════════════════════
    # EJE 1.3 — SERVICIOS SOCIALES (servicios básicos)
    # ═══════════════════════════════════════════════════════════════════════
    "Servicios Sociales": {
        "tipo": "eje",
        "codigo": "1.3",
        "servicios": {

            # ─── Servicio 1.3.1 — Servicios sociales y complementarios ───
            # Planificación: 4  |  Ejecución: 5  |  Evaluación: 3  |  TOTAL: 12
            "Servicios sociales y complementarios": {
                "codigo_servicio": "1.3.1",
                "agrupacion": "Básico",
                "etapas": {
                    "Planificación": [
                        {"codigo": "1.3.1.1", "nombre": "Reglamento de servicios sociales y complementarios", "tipo": TIPO_BINARIO, "evidencia": True, "doc": "Reglamento vigente"},
                        {"codigo": "1.3.1.2", "nombre": "Plan de servicios sociales cantonal", "tipo": TIPO_BINARIO, "evidencia": True, "doc": "Plan de servicios sociales vigente"},
                        {"codigo": "1.3.1.3", "nombre": "Identificación y caracterización de grupos en condición de vulnerabilidad", "tipo": TIPO_BINARIO, "evidencia": False},
                        {"codigo": "1.3.1.4", "nombre": "Articulación con redes institucionales de apoyo social (IMAS, CCSS, otros)", "tipo": TIPO_BINARIO, "evidencia": False},
                    ],
                    "Ejecución": [
                        {"codigo": "1.3.1.5", "nombre": "Cobertura de servicios sociales por distrito", "tipo": TIPO_COBERTURA, "evidencia": False},
                        {"codigo": "1.3.1.6", "nombre": "Atención directa a población en condición de vulnerabilidad", "tipo": TIPO_BINARIO, "evidencia": False},
                        {"codigo": "1.3.1.7", "nombre": "Programas de atención a adultos mayores, personas con discapacidad y niñez", "tipo": TIPO_BINARIO, "evidencia": False},
                        {"codigo": "1.3.1.8", "nombre": "Nivel de ejecución de los recursos del servicio social", "tipo": TIPO_PORCENTAJE, "evidencia": False},
                        {"codigo": "1.3.1.9", "nombre": "Inclusión del enfoque de género en la prestación de servicios sociales", "tipo": TIPO_BINARIO, "evidencia": False},
                    ],
                    "Evaluación": [
                        {"codigo": "1.3.1.10", "nombre": "Evaluación del impacto de los servicios sociales cantonales", "tipo": TIPO_BINARIO, "evidencia": False},
                        {"codigo": "1.3.1.11", "nombre": "Satisfacción de los usuarios de los servicios sociales", "tipo": TIPO_BINARIO, "evidencia": True, "doc": "Estudio de satisfacción del usuario"},
                        {"codigo": "1.3.1.12", "nombre": "Plan de mejora de los servicios sociales y complementarios", "tipo": TIPO_BINARIO, "evidencia": True, "doc": "Plan de mejora vigente"},
                    ],
                },
            },

            # ─── Servicio 1.3.2 — Servicios educativos, culturales y deportivos ───
            # Planificación: 6  |  Ejecución: 5  |  Evaluación: 3  |  TOTAL: 14
            "Servicios educativos, culturales y deportivos": {
                "codigo_servicio": "1.3.2",
                "agrupacion": "Básico",
                "etapas": {
                    "Planificación": [
                        {"codigo": "1.3.2.1", "nombre": "Reglamento de servicios educativos, culturales y deportivos", "tipo": TIPO_BINARIO, "evidencia": True, "doc": "Reglamento vigente"},
                        {"codigo": "1.3.2.2", "nombre": "Plan cantonal de cultura y deporte", "tipo": TIPO_BINARIO, "evidencia": True, "doc": "Plan cantonal vigente"},
                        {"codigo": "1.3.2.3", "nombre": "Identificación de necesidades culturales y deportivas del cantón", "tipo": TIPO_BINARIO, "evidencia": False},
                        {"codigo": "1.3.2.4", "nombre": "Inventario de infraestructura cultural, educativa y deportiva cantonal", "tipo": TIPO_BINARIO, "evidencia": False},
                        {"codigo": "1.3.2.5", "nombre": "Presupuesto destinado a servicios culturales y deportivos", "tipo": TIPO_PORCENTAJE, "evidencia": False},
                        {"codigo": "1.3.2.6", "nombre": "Coordinación con entidades educativas y culturales nacionales", "tipo": TIPO_BINARIO, "evidencia": False},
                    ],
                    "Ejecución": [
                        {"codigo": "1.3.2.7",  "nombre": "Ejecución de programas culturales, recreativos y deportivos", "tipo": TIPO_BINARIO, "evidencia": False},
                        {"codigo": "1.3.2.8",  "nombre": "Mantenimiento de infraestructura cultural, educativa y deportiva", "tipo": TIPO_BINARIO, "evidencia": False},
                        {"codigo": "1.3.2.9",  "nombre": "Nivel de ejecución de los recursos del servicio", "tipo": TIPO_PORCENTAJE, "evidencia": False},
                        {"codigo": "1.3.2.10", "nombre": "Cobertura de actividades culturales y deportivas por distrito", "tipo": TIPO_COBERTURA, "evidencia": False},
                        {"codigo": "1.3.2.11", "nombre": "Inclusión de grupos vulnerables en actividades culturales y deportivas", "tipo": TIPO_BINARIO, "evidencia": False},
                    ],
                    "Evaluación": [
                        {"codigo": "1.3.2.12", "nombre": "Evaluación del impacto de programas culturales, educativos y deportivos", "tipo": TIPO_BINARIO, "evidencia": False},
                        {"codigo": "1.3.2.13", "nombre": "Satisfacción de los participantes en actividades culturales y deportivas", "tipo": TIPO_BINARIO, "evidencia": True, "doc": "Estudio de satisfacción de participantes"},
                        {"codigo": "1.3.2.14", "nombre": "Plan de mejora de los servicios culturales, educativos y deportivos", "tipo": TIPO_BINARIO, "evidencia": True, "doc": "Plan de mejora vigente"},
                    ],
                },
            },
        },
    },

    # ═══════════════════════════════════════════════════════════════════════
    # EJE 2 — SERVICIOS ESPECIALIZADOS (diversificados)
    # ═══════════════════════════════════════════════════════════════════════
    "Servicios Especializados": {
        "tipo": "eje",
        "codigo": "2",
        "servicios": {

            # ─── Servicio 2.1.1 — Agua potable ───
            # Planificación: 7  |  Ejecución: 7  |  Evaluación: 3  |  TOTAL: 17
            "Agua potable": {
                "codigo_servicio": "2.1.1",
                "agrupacion": "Diversificado",
                "diversificado_key": "agua_potable",
                "etapas": {
                    "Planificación": [
                        {"codigo": "2.1.1.1", "nombre": "Reglamento del servicio de agua potable municipal", "tipo": TIPO_BINARIO, "evidencia": True, "doc": "Reglamento vigente del servicio de agua"},
                        {"codigo": "2.1.1.2", "nombre": "Plan maestro de agua potable cantonal", "tipo": TIPO_BINARIO, "evidencia": True, "doc": "Plan maestro actualizado"},
                        {"codigo": "2.1.1.3", "nombre": "Diagnóstico del sistema de abastecimiento de agua potable", "tipo": TIPO_BINARIO, "evidencia": True, "doc": "Diagnóstico técnico del sistema"},
                        {"codigo": "2.1.1.4", "nombre": "Actualización de la tarifa del servicio de agua potable", "tipo": TIPO_BINARIO, "evidencia": True, "doc": "Tarifa aprobada y vigente"},
                        {"codigo": "2.1.1.5", "nombre": "Identificación y protección de fuentes de agua del cantón", "tipo": TIPO_BINARIO, "evidencia": False},
                        {"codigo": "2.1.1.6", "nombre": "Plan de gestión de la demanda y conservación del agua", "tipo": TIPO_BINARIO, "evidencia": False},
                        {"codigo": "2.1.1.7", "nombre": "Identificación de la población vulnerable para el servicio de agua", "tipo": TIPO_BINARIO, "evidencia": False},
                    ],
                    "Ejecución": [
                        {"codigo": "2.1.1.8",  "nombre": "Cobertura del servicio de agua potable por distrito", "tipo": TIPO_COBERTURA, "evidencia": False},
                        {"codigo": "2.1.1.9",  "nombre": "Calidad del agua distribuida (análisis bacteriológicos y fisicoquímicos)", "tipo": TIPO_BINARIO, "evidencia": True, "doc": "Análisis de calidad del agua vigentes"},
                        {"codigo": "2.1.1.10", "nombre": "Continuidad del servicio de agua potable (horas/día)", "tipo": TIPO_PORCENTAJE, "evidencia": False},
                        {"codigo": "2.1.1.11", "nombre": "Nivel de ejecución de los recursos del servicio de agua", "tipo": TIPO_PORCENTAJE, "evidencia": False},
                        {"codigo": "2.1.1.12", "nombre": "Inversión en infraestructura y mantenimiento del sistema de agua", "tipo": TIPO_PORCENTAJE, "evidencia": False},
                        {"codigo": "2.1.1.13", "nombre": "Morosidad del servicio de agua potable", "tipo": TIPO_PORCENTAJE, "evidencia": False},
                        {"codigo": "2.1.1.14", "nombre": "Control de pérdidas en la red de distribución de agua", "tipo": TIPO_PORCENTAJE, "evidencia": False},
                    ],
                    "Evaluación": [
                        {"codigo": "2.1.1.15", "nombre": "Evaluación técnica del sistema de agua potable", "tipo": TIPO_BINARIO, "evidencia": False},
                        {"codigo": "2.1.1.16", "nombre": "Satisfacción del usuario del servicio de agua potable", "tipo": TIPO_BINARIO, "evidencia": True, "doc": "Estudio de satisfacción del usuario"},
                        {"codigo": "2.1.1.17", "nombre": "Plan de mejora del servicio de agua potable", "tipo": TIPO_BINARIO, "evidencia": True, "doc": "Plan de mejora vigente con avances"},
                    ],
                },
            },

            # ─── Servicio 2.2.1 — Zona Marítimo Terrestre (ZMT) ───
            # Planificación: 5  |  Ejecución: 6  |  Evaluación: 2  |  TOTAL: 13
            "Zona Marítimo Terrestre": {
                "codigo_servicio": "2.2.1",
                "agrupacion": "Diversificado",
                "diversificado_key": "zmt",
                "etapas": {
                    "Planificación": [
                        {"codigo": "2.2.1.1", "nombre": "Plan regulador de la Zona Marítimo Terrestre (ZMT)", "tipo": TIPO_BINARIO, "evidencia": True, "doc": "Plan regulador ZMT aprobado"},
                        {"codigo": "2.2.1.2", "nombre": "Reglamento de administración y gestión de la ZMT", "tipo": TIPO_BINARIO, "evidencia": True, "doc": "Reglamento vigente de la ZMT"},
                        {"codigo": "2.2.1.3", "nombre": "Catastro actualizado de la Zona Marítimo Terrestre", "tipo": TIPO_BINARIO, "evidencia": True, "doc": "Catastro de concesiones actualizado"},
                        {"codigo": "2.2.1.4", "nombre": "Sistema de cobro de cánones de la ZMT", "tipo": TIPO_BINARIO, "evidencia": False},
                        {"codigo": "2.2.1.5", "nombre": "Presupuesto destinado a la administración de la ZMT", "tipo": TIPO_PORCENTAJE, "evidencia": False},
                    ],
                    "Ejecución": [
                        {"codigo": "2.2.1.6",  "nombre": "Inspecciones de la ZMT realizadas", "tipo": TIPO_BINARIO, "evidencia": False},
                        {"codigo": "2.2.1.7",  "nombre": "Control de construcciones ilegales en la ZMT", "tipo": TIPO_BINARIO, "evidencia": False},
                        {"codigo": "2.2.1.8",  "nombre": "Nivel de ejecución de los recursos de la ZMT", "tipo": TIPO_PORCENTAJE, "evidencia": False},
                        {"codigo": "2.2.1.9",  "nombre": "Recuperación del canon de concesiones de la ZMT", "tipo": TIPO_PORCENTAJE, "evidencia": False},
                        {"codigo": "2.2.1.10", "nombre": "Atención de denuncias sobre uso de la ZMT", "tipo": TIPO_BINARIO, "evidencia": False},
                        {"codigo": "2.2.1.11", "nombre": "Actualización de concesiones de la ZMT", "tipo": TIPO_BINARIO, "evidencia": False},
                    ],
                    "Evaluación": [
                        {"codigo": "2.2.1.12", "nombre": "Evaluación del plan regulador y gestión de la ZMT", "tipo": TIPO_BINARIO, "evidencia": False},
                        {"codigo": "2.2.1.13", "nombre": "Plan de mejora de la gestión de la ZMT", "tipo": TIPO_BINARIO, "evidencia": True, "doc": "Plan de mejora de la ZMT vigente"},
                    ],
                },
            },

            # ─── Servicio 2.3.1 — Seguridad y vigilancia ───
            # Planificación: 5  |  Ejecución: 4  |  Evaluación: 7  |  TOTAL: 16
            "Seguridad y vigilancia": {
                "codigo_servicio": "2.3.1",
                "agrupacion": "Diversificado",
                "diversificado_key": "seguridad",
                "etapas": {
                    "Planificación": [
                        {"codigo": "2.3.1.1", "nombre": "Reglamento del servicio de seguridad y vigilancia municipal", "tipo": TIPO_BINARIO, "evidencia": True, "doc": "Reglamento vigente del servicio"},
                        {"codigo": "2.3.1.2", "nombre": "Plan cantonal de seguridad ciudadana", "tipo": TIPO_BINARIO, "evidencia": True, "doc": "Plan de seguridad ciudadana vigente"},
                        {"codigo": "2.3.1.3", "nombre": "Diagnóstico de seguridad cantonal actualizado", "tipo": TIPO_BINARIO, "evidencia": True, "doc": "Diagnóstico de seguridad del cantón"},
                        {"codigo": "2.3.1.4", "nombre": "Coordinación interinstitucional en materia de seguridad (Fuerza Pública, OIJ)", "tipo": TIPO_BINARIO, "evidencia": False},
                        {"codigo": "2.3.1.5", "nombre": "Presupuesto destinado al servicio de seguridad y vigilancia", "tipo": TIPO_PORCENTAJE, "evidencia": False},
                    ],
                    "Ejecución": [
                        {"codigo": "2.3.1.6", "nombre": "Cobertura del servicio de seguridad y vigilancia por distrito", "tipo": TIPO_COBERTURA, "evidencia": False},
                        {"codigo": "2.3.1.7", "nombre": "Nivel de ejecución de los recursos disponibles del servicio", "tipo": TIPO_PORCENTAJE, "evidencia": False},
                        {"codigo": "2.3.1.8", "nombre": "Atención oportuna de denuncias de seguridad", "tipo": TIPO_BINARIO, "evidencia": False},
                        {"codigo": "2.3.1.9", "nombre": "Programas de prevención del delito y convivencia pacífica", "tipo": TIPO_BINARIO, "evidencia": False},
                    ],
                    "Evaluación": [
                        {"codigo": "2.3.1.10", "nombre": "Percepción ciudadana de seguridad en el cantón", "tipo": TIPO_BINARIO, "evidencia": True, "doc": "Estudio de percepción ciudadana de seguridad"},
                        {"codigo": "2.3.1.11", "nombre": "Evaluación del plan cantonal de seguridad", "tipo": TIPO_BINARIO, "evidencia": False},
                        {"codigo": "2.3.1.12", "nombre": "Reducción de índices delictivos en el cantón", "tipo": TIPO_PORCENTAJE, "evidencia": False},
                        {"codigo": "2.3.1.13", "nombre": "Plan de mejora del servicio de seguridad y vigilancia", "tipo": TIPO_BINARIO, "evidencia": True, "doc": "Plan de mejora vigente del servicio"},
                        {"codigo": "2.3.1.14", "nombre": "Implementación del plan de mejora del servicio de seguridad", "tipo": TIPO_BINARIO, "evidencia": False},
                        {"codigo": "2.3.1.15", "nombre": "Infraestructura tecnológica de vigilancia (cámaras, sistemas)", "tipo": TIPO_BINARIO, "evidencia": False},
                        {"codigo": "2.3.1.16", "nombre": "Inclusión del enfoque de género en la evaluación del servicio de seguridad", "tipo": TIPO_BINARIO, "evidencia": False},
                    ],
                },
            },
        },
    },
}


def get_servicios_para_municipalidad(diversificados: list) -> dict:
    """Return the services that apply to a municipality.

    Basic services are always included. Diversified services are included only
    when their service key is present in the municipality's diversified-service
    list.

    Args:
        diversificados: Diversified service keys assigned to the municipality.

    Returns:
        Mapping from service name to service metadata, including the axis name.
    """

    servicios = {}
    for eje_nombre, eje_data in ESTRUCTURA_IGSM.items():
        for serv_nombre, serv_data in eje_data["servicios"].items():
            if serv_data["agrupacion"] == "Básico":
                servicios[serv_nombre] = {**serv_data, "eje": eje_nombre}
            elif serv_data.get("diversificado_key") in diversificados:
                servicios[serv_nombre] = {**serv_data, "eje": eje_nombre}
    return servicios


def contar_indicadores_totales() -> dict:
    """Count scored indicators by stage and in total.

    Returns:
        Dictionary with total, planning, execution, and evaluation counts.
    """

    total = plan = ejec = evalu = 0
    for eje_data in ESTRUCTURA_IGSM.values():
        for serv_data in eje_data["servicios"].values():
            for etapa, inds in serv_data["etapas"].items():
                count = len([i for i in inds if i["tipo"] != TIPO_INFORMATIVO])
                total += count
                if etapa == "Planificación":  plan  += count
                elif etapa == "Ejecución":    ejec  += count
                elif etapa == "Evaluación":   evalu += count
    return {"total": total, "planificacion": plan, "ejecucion": ejec, "evaluacion": evalu}
