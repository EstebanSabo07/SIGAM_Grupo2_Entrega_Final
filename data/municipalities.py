"""Static municipality catalog for Costa Rica."""

# data/municipalities.py — 84 municipalidades de Costa Rica con coordenadas y regiones

MUNICIPALIDADES = [
    # San José
    {"codigo": "101", "nombre": "San José",         "provincia": "San José",   "region": "Central",    "lat": 9.9281,  "lon": -84.0907, "diversificados": []},
    {"codigo": "102", "nombre": "Escazú",            "provincia": "San José",   "region": "Central",    "lat": 9.9189,  "lon": -84.1400, "diversificados": ["seguridad"]},
    {"codigo": "103", "nombre": "Desamparados",      "provincia": "San José",   "region": "Central",    "lat": 9.8980,  "lon": -84.0680, "diversificados": []},
    {"codigo": "104", "nombre": "Puriscal",          "provincia": "San José",   "region": "Pacífico Central", "lat": 9.8417, "lon": -84.3178, "diversificados": []},
    {"codigo": "105", "nombre": "Tarrazú",           "provincia": "San José",   "region": "Brunca",     "lat": 9.6692,  "lon": -84.0603, "diversificados": []},
    {"codigo": "106", "nombre": "Aserrí",            "provincia": "San José",   "region": "Central",    "lat": 9.8544,  "lon": -84.1084, "diversificados": []},
    {"codigo": "107", "nombre": "Mora",              "provincia": "San José",   "region": "Central",    "lat": 9.9003,  "lon": -84.2811, "diversificados": []},
    {"codigo": "108", "nombre": "Goicoechea",        "provincia": "San José",   "region": "Central",    "lat": 9.9567,  "lon": -84.0278, "diversificados": []},
    {"codigo": "109", "nombre": "Santa Ana",         "provincia": "San José",   "region": "Central",    "lat": 9.9311,  "lon": -84.1850, "diversificados": []},
    {"codigo": "110", "nombre": "Alajuelita",        "provincia": "San José",   "region": "Central",    "lat": 9.9000,  "lon": -84.1067, "diversificados": []},
    {"codigo": "111", "nombre": "Vásquez de Coronado","provincia": "San José",  "region": "Central",    "lat": 9.9989,  "lon": -83.9967, "diversificados": []},
    {"codigo": "112", "nombre": "Acosta",            "provincia": "San José",   "region": "Central",    "lat": 9.7522,  "lon": -84.2114, "diversificados": []},
    {"codigo": "113", "nombre": "Tibás",             "provincia": "San José",   "region": "Central",    "lat": 9.9689,  "lon": -84.0736, "diversificados": []},
    {"codigo": "114", "nombre": "Moravia",           "provincia": "San José",   "region": "Central",    "lat": 9.9742,  "lon": -83.9989, "diversificados": []},
    {"codigo": "115", "nombre": "Montes de Oca",     "provincia": "San José",   "region": "Central",    "lat": 9.9348,  "lon": -83.9970, "diversificados": []},
    {"codigo": "116", "nombre": "Turrubares",        "provincia": "San José",   "region": "Pacífico Central", "lat": 9.8039, "lon": -84.5331, "diversificados": []},
    {"codigo": "117", "nombre": "Dota",              "provincia": "San José",   "region": "Brunca",     "lat": 9.6597,  "lon": -83.9669, "diversificados": []},
    {"codigo": "118", "nombre": "Curridabat",        "provincia": "San José",   "region": "Central",    "lat": 9.9186,  "lon": -83.9968, "diversificados": []},
    {"codigo": "119", "nombre": "Pérez Zeledón",     "provincia": "San José",   "region": "Brunca",     "lat": 9.3613,  "lon": -83.6592, "diversificados": []},
    {"codigo": "120", "nombre": "León Cortés",       "provincia": "San José",   "region": "Central",    "lat": 9.7608,  "lon": -84.0617, "diversificados": []},
    # Alajuela
    {"codigo": "201", "nombre": "Alajuela",          "provincia": "Alajuela",   "region": "Central",    "lat": 10.0167, "lon": -84.2167, "diversificados": ["agua_potable", "seguridad"]},
    {"codigo": "202", "nombre": "San Ramón",         "provincia": "Alajuela",   "region": "Huetar Norte","lat": 10.0900, "lon": -84.4700, "diversificados": []},
    {"codigo": "203", "nombre": "Grecia",            "provincia": "Alajuela",   "region": "Central",    "lat": 10.0689, "lon": -84.3142, "diversificados": ["agua_potable"]},
    {"codigo": "204", "nombre": "San Mateo",         "provincia": "Alajuela",   "region": "Pacífico Central","lat": 9.9967,"lon": -84.5133, "diversificados": []},
    {"codigo": "205", "nombre": "Atenas",            "provincia": "Alajuela",   "region": "Pacífico Central","lat": 9.9828,"lon": -84.3789, "diversificados": []},
    {"codigo": "206", "nombre": "Naranjo",           "provincia": "Alajuela",   "region": "Central",    "lat": 10.1028, "lon": -84.3939, "diversificados": []},
    {"codigo": "207", "nombre": "Palmares",          "provincia": "Alajuela",   "region": "Central",    "lat": 10.0606, "lon": -84.4350, "diversificados": []},
    {"codigo": "208", "nombre": "Poás",              "provincia": "Alajuela",   "region": "Central",    "lat": 10.0467, "lon": -84.2344, "diversificados": []},
    {"codigo": "209", "nombre": "Orotina",           "provincia": "Alajuela",   "region": "Pacífico Central","lat": 9.9069,"lon": -84.5247, "diversificados": []},
    {"codigo": "210", "nombre": "San Carlos",        "provincia": "Alajuela",   "region": "Huetar Norte","lat": 10.3367, "lon": -84.5144, "diversificados": ["agua_potable"]},
    {"codigo": "211", "nombre": "Alfaro Ruiz",       "provincia": "Alajuela",   "region": "Central",    "lat": 10.1942, "lon": -84.3703, "diversificados": []},
    {"codigo": "212", "nombre": "Valverde Vega",     "provincia": "Alajuela",   "region": "Central",    "lat": 10.1431, "lon": -84.4369, "diversificados": []},
    {"codigo": "213", "nombre": "Upala",             "provincia": "Alajuela",   "region": "Huetar Norte","lat": 10.8958, "lon": -85.0167, "diversificados": []},
    {"codigo": "214", "nombre": "Los Chiles",        "provincia": "Alajuela",   "region": "Huetar Norte","lat": 11.0331, "lon": -84.7150, "diversificados": []},
    {"codigo": "215", "nombre": "Guatuso",           "provincia": "Alajuela",   "region": "Huetar Norte","lat": 10.6839, "lon": -84.8322, "diversificados": []},
    {"codigo": "216", "nombre": "Río Cuarto",        "provincia": "Alajuela",   "region": "Huetar Norte","lat": 10.5989, "lon": -84.1928, "diversificados": []},
    # Cartago
    {"codigo": "301", "nombre": "Cartago",           "provincia": "Cartago",    "region": "Central",    "lat": 9.8645,  "lon": -83.9197, "diversificados": ["agua_potable"]},
    {"codigo": "302", "nombre": "Paraíso",           "provincia": "Cartago",    "region": "Central",    "lat": 9.8369,  "lon": -83.8651, "diversificados": []},
    {"codigo": "303", "nombre": "La Unión",          "provincia": "Cartago",    "region": "Central",    "lat": 9.9131,  "lon": -83.9814, "diversificados": []},
    {"codigo": "304", "nombre": "Jiménez",           "provincia": "Cartago",    "region": "Central",    "lat": 9.7792,  "lon": -83.7367, "diversificados": []},
    {"codigo": "305", "nombre": "Turrialba",         "provincia": "Cartago",    "region": "Huetar Caribe","lat": 9.9021, "lon": -83.6814, "diversificados": ["agua_potable"]},
    {"codigo": "306", "nombre": "Alvarado",          "provincia": "Cartago",    "region": "Central",    "lat": 9.8831,  "lon": -83.8403, "diversificados": []},
    {"codigo": "307", "nombre": "Oreamuno",          "provincia": "Cartago",    "region": "Central",    "lat": 9.8786,  "lon": -83.8900, "diversificados": []},
    {"codigo": "308", "nombre": "El Guarco",         "provincia": "Cartago",    "region": "Central",    "lat": 9.8039,  "lon": -83.9864, "diversificados": []},
    # Heredia
    {"codigo": "401", "nombre": "Heredia",           "provincia": "Heredia",    "region": "Central",    "lat": 9.9983,  "lon": -84.1170, "diversificados": ["agua_potable"]},
    {"codigo": "402", "nombre": "Barva",             "provincia": "Heredia",    "region": "Central",    "lat": 10.0281, "lon": -84.1364, "diversificados": []},
    {"codigo": "403", "nombre": "Santo Domingo",     "provincia": "Heredia",    "region": "Central",    "lat": 9.9800,  "lon": -84.0942, "diversificados": []},
    {"codigo": "404", "nombre": "Santa Bárbara",     "provincia": "Heredia",    "region": "Central",    "lat": 10.0322, "lon": -84.1681, "diversificados": []},
    {"codigo": "405", "nombre": "San Rafael",        "provincia": "Heredia",    "region": "Central",    "lat": 10.0219, "lon": -84.1028, "diversificados": []},
    {"codigo": "406", "nombre": "San Isidro",        "provincia": "Heredia",    "region": "Central",    "lat": 10.0000, "lon": -84.0547, "diversificados": []},
    {"codigo": "407", "nombre": "Belén",             "provincia": "Heredia",    "region": "Central",    "lat": 9.9703,  "lon": -84.1817, "diversificados": []},
    {"codigo": "408", "nombre": "Flores",            "provincia": "Heredia",    "region": "Central",    "lat": 10.0011, "lon": -84.1594, "diversificados": []},
    {"codigo": "409", "nombre": "San Pablo",         "provincia": "Heredia",    "region": "Central",    "lat": 10.0106, "lon": -84.0906, "diversificados": []},
    {"codigo": "410", "nombre": "Sarapiquí",         "provincia": "Heredia",    "region": "Huetar Norte","lat": 10.4856, "lon": -84.0108, "diversificados": []},
    # Guanacaste
    {"codigo": "501", "nombre": "Liberia",           "provincia": "Guanacaste", "region": "Chorotega",  "lat": 10.6333, "lon": -85.4333, "diversificados": ["agua_potable", "zmt", "seguridad"]},
    {"codigo": "502", "nombre": "Nicoya",            "provincia": "Guanacaste", "region": "Chorotega",  "lat": 10.1500, "lon": -85.4500, "diversificados": ["zmt"]},
    {"codigo": "503", "nombre": "Santa Cruz",        "provincia": "Guanacaste", "region": "Chorotega",  "lat": 10.2667, "lon": -85.5833, "diversificados": ["zmt"]},
    {"codigo": "504", "nombre": "Bagaces",           "provincia": "Guanacaste", "region": "Chorotega",  "lat": 10.5261, "lon": -85.2522, "diversificados": []},
    {"codigo": "505", "nombre": "Carrillo",          "provincia": "Guanacaste", "region": "Chorotega",  "lat": 10.4331, "lon": -85.6117, "diversificados": ["zmt"]},
    {"codigo": "506", "nombre": "Cañas",             "provincia": "Guanacaste", "region": "Chorotega",  "lat": 10.4233, "lon": -85.1097, "diversificados": []},
    {"codigo": "507", "nombre": "Abangares",         "provincia": "Guanacaste", "region": "Chorotega",  "lat": 10.2928, "lon": -85.0267, "diversificados": []},
    {"codigo": "508", "nombre": "Tilarán",           "provincia": "Guanacaste", "region": "Chorotega",  "lat": 10.4658, "lon": -84.9742, "diversificados": []},
    {"codigo": "509", "nombre": "Nandayure",         "provincia": "Guanacaste", "region": "Chorotega",  "lat": 9.9200,  "lon": -85.3233, "diversificados": ["zmt"]},
    {"codigo": "510", "nombre": "La Cruz",           "provincia": "Guanacaste", "region": "Chorotega",  "lat": 11.0700, "lon": -85.6233, "diversificados": []},
    {"codigo": "511", "nombre": "Hojancha",          "provincia": "Guanacaste", "region": "Chorotega",  "lat": 10.1317, "lon": -85.3900, "diversificados": ["zmt"]},
    # Puntarenas
    {"codigo": "601", "nombre": "Puntarenas",        "provincia": "Puntarenas", "region": "Pacífico Central","lat": 9.9781, "lon": -84.8417, "diversificados": ["agua_potable", "zmt"]},
    {"codigo": "602", "nombre": "Esparza",           "provincia": "Puntarenas", "region": "Pacífico Central","lat": 9.9875, "lon": -84.6617, "diversificados": []},
    {"codigo": "603", "nombre": "Buenos Aires",      "provincia": "Puntarenas", "region": "Brunca",     "lat": 9.1781,  "lon": -83.3125, "diversificados": []},
    {"codigo": "604", "nombre": "Montes de Oro",     "provincia": "Puntarenas", "region": "Pacífico Central","lat": 10.0467,"lon": -84.5911, "diversificados": []},
    {"codigo": "605", "nombre": "Osa",               "provincia": "Puntarenas", "region": "Brunca",     "lat": 8.9369,  "lon": -83.5633, "diversificados": ["zmt"]},
    {"codigo": "606", "nombre": "Quepos",            "provincia": "Puntarenas", "region": "Pacífico Central","lat": 9.4267, "lon": -84.1633, "diversificados": ["zmt"]},
    {"codigo": "607", "nombre": "Golfito",           "provincia": "Puntarenas", "region": "Brunca",     "lat": 8.6317,  "lon": -83.1778, "diversificados": ["zmt"]},
    {"codigo": "608", "nombre": "Coto Brus",         "provincia": "Puntarenas", "region": "Brunca",     "lat": 8.9217,  "lon": -82.9658, "diversificados": []},
    {"codigo": "609", "nombre": "Parrita",           "provincia": "Puntarenas", "region": "Pacífico Central","lat": 9.5200, "lon": -84.3267, "diversificados": ["zmt"]},
    {"codigo": "610", "nombre": "Corredores",        "provincia": "Puntarenas", "region": "Brunca",     "lat": 8.5369,  "lon": -83.0333, "diversificados": []},
    {"codigo": "611", "nombre": "Garabito",          "provincia": "Puntarenas", "region": "Pacífico Central","lat": 9.5908, "lon": -84.6633, "diversificados": ["zmt"]},
    {"codigo": "612", "nombre": "Monteverde",        "provincia": "Puntarenas", "region": "Pacífico Central","lat": 10.3011,"lon": -84.8231, "diversificados": ["zmt"]},
    {"codigo": "613", "nombre": "Puerto Jiménez",   "provincia": "Puntarenas", "region": "Brunca",     "lat": 8.5333,  "lon": -83.3000, "diversificados": []},
    # Limón
    {"codigo": "701", "nombre": "Limón",             "provincia": "Limón",      "region": "Huetar Caribe","lat": 10.0000, "lon": -83.0333, "diversificados": ["agua_potable"]},
    {"codigo": "702", "nombre": "Pococí",            "provincia": "Limón",      "region": "Huetar Caribe","lat": 10.4497, "lon": -83.7408, "diversificados": []},
    {"codigo": "703", "nombre": "Siquirres",         "provincia": "Limón",      "region": "Huetar Caribe","lat": 10.1028, "lon": -83.5083, "diversificados": []},
    {"codigo": "704", "nombre": "Talamanca",         "provincia": "Limón",      "region": "Huetar Caribe","lat": 9.5833,  "lon": -82.9286, "diversificados": ["zmt"]},
    {"codigo": "705", "nombre": "Matina",            "provincia": "Limón",      "region": "Huetar Caribe","lat": 10.0731, "lon": -83.3347, "diversificados": []},
    {"codigo": "706", "nombre": "Guácimo",           "provincia": "Limón",      "region": "Huetar Caribe","lat": 10.2228, "lon": -83.6822, "diversificados": []},
]

# Códigos de acceso por municipalidad (en producción vendrían de Firestore)
CODIGOS_ACCESO = {m["codigo"]: m["codigo"][-4:].zfill(4) for m in MUNICIPALIDADES}

REGIONES = sorted(list(set(m["region"] for m in MUNICIPALIDADES)))

PROVINCIAS = ["San José", "Alajuela", "Cartago", "Heredia", "Guanacaste", "Puntarenas", "Limón"]

def get_municipalidad(codigo: str) -> dict:
    """Return a municipality by code.

    Args:
        codigo: Municipality code.

    Returns:
        Municipality dictionary, or None when not found.
    """

    for m in MUNICIPALIDADES:
        if m["codigo"] == codigo:
            return m
    return None

def get_municipalidades_by_region(region: str) -> list:
    """Return municipalities in a region.

    Args:
        region: Region name.

    Returns:
        List of municipality dictionaries for the region.
    """

    return [m for m in MUNICIPALIDADES if m["region"] == region]

def get_nombres() -> list:
    """Return all municipality names.

    Returns:
        List of municipality names in catalog order.
    """

    return [m["nombre"] for m in MUNICIPALIDADES]

def get_by_nombre(nombre: str) -> dict:
    """Return a municipality by exact name.

    Args:
        nombre: Municipality name.

    Returns:
        Municipality dictionary, or None when not found.
    """

    for m in MUNICIPALIDADES:
        if m["nombre"] == nombre:
            return m
    return None
