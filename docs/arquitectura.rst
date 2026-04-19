Arquitectura
============

SIGAM esta organizado como una aplicacion Streamlit modular. El archivo
``main.py`` configura la pagina, carga estilos globales y enruta entre vistas
segun ``st.session_state``. Para evitar efectos secundarios durante la
generacion de documentacion, ``main.py`` se describe en esta pagina y no se
incluye en la referencia autodoc.

Capas principales
-----------------

``views/``
   Pantallas Streamlit para landing, login, portal municipal, dashboard
   administrativo, analisis, gestion de pesos y exportacion.

``components/``
   Componentes reutilizables de interfaz y funciones para crear graficos
   Plotly.

``data/``
   Estructura estatica del IGSM, catalogo municipal, calculos, datos simulados
   de respaldo y capa adaptadora para las vistas.

``database/``
   Modelos SQLAlchemy, sesiones, repositorios, inicializacion, siembra de datos
   e importacion del baseline desde CSV.

Flujo general
-------------

1. El usuario entra por ``main.py``.
2. La sesion determina si se muestra landing, login, portal municipal o portal
   administrativo.
3. Las vistas consultan datos mediante ``data.db_layer``.
4. ``data.db_layer`` adapta las llamadas hacia ``database.repositories`` y
   devuelve estructuras listas para la interfaz.
5. Los calculos de puntajes se apoyan en la estructura IGSM y en las respuestas
   persistidas.
