Base de Datos
=============

La capa de persistencia usa SQLAlchemy ORM con un modelo dimensional para
municipalidades, ejes, servicios, etapas, indicadores y respuestas.

Entidades principales
---------------------

* ``dm_municipality``: catalogo de municipalidades con provincia, region y
  coordenadas.
* ``dm_axis``: ejes de gestion IGSM.
* ``dm_service``: servicios municipales basicos y diversificados.
* ``dm_stage``: etapas de planificacion, ejecucion y evaluacion.
* ``dm_indicator``: indicadores oficiales del formulario.
* ``fact_indicator_response``: respuestas numericas por municipalidad e
  indicador.
* ``fact_stage_weight``: pesos de etapa con vigencia.
* ``fact_maturity_threshold``: umbrales de madurez con vigencia.

Inicializacion
--------------

El comando ``python -m database.init_db`` crea el esquema configurado y carga
datos de referencia. El importador ``database.import_source_baseline`` carga los
CSV ubicados en ``database/source`` y registra el baseline de respuestas.

Configuracion
-------------

La variable de entorno ``DATABASE_URL`` define la base activa. Si no se define,
el proyecto usa SQLite local en ``database/igsm_dev.sqlite3``.
