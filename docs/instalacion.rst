Instalacion y Ejecucion
=======================

Requisitos
----------

* Python 3.11 o superior.
* Dependencias de ejecucion listadas en ``requirements.txt``.
* Dependencias de documentacion listadas en ``docs/requirements.txt``.

Aplicacion local
----------------

Desde la raiz del repositorio:

.. code-block:: bash

   pip install -r requirements.txt
   python -m database.init_db
   python -m database.import_source_baseline --period 2025
   streamlit run main.py

La aplicacion se abre normalmente en ``http://localhost:8501``.

Documentacion Sphinx
--------------------

Para construir la documentacion HTML:

.. code-block:: bash

   pip install -r docs/requirements.txt
   sphinx-build -b html docs docs/_build/html

El resultado se genera en ``docs/_build/html``. Ese directorio es salida de
build y no forma parte de la documentacion fuente.
