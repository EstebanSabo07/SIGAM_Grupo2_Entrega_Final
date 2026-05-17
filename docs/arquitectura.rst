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
   Servicios de snapshot, presentacion, reportes, catalogo y respuestas sobre
   la estructura IGSM respaldada por el ORM.

``database/``
   Modelos SQLAlchemy, sesiones, repositorios, inicializacion, siembra de datos
   e importacion del baseline desde CSV.

Flujo general
-------------

1. El usuario entra por ``main.py``.
2. La sesion determina si se muestra landing, login, portal municipal o portal
   administrativo.
3. Las vistas crean un ``SnapshotContext`` con el mes de corte y la audiencia.
4. Los servicios en ``data/`` consultan ``database.repositories`` y devuelven
   view-models listos para la interfaz segun la audiencia.
5. Los calculos de puntajes y niveles usan respuestas persistidas y la fecha de
   corte del snapshot.
