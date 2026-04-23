#!/bin/bash
set -e
DB_PATH="database/igsm_dev.sqlite3"
if [ ! -f "$DB_PATH" ]; then
    echo "Inicializando base de datos..."
    python -m database.init_db
    python -m database.import_source_baseline
    echo "Base de datos lista."
fi
exec streamlit run main.py --server.port=8080 --server.address=0.0.0.0 --server.headless=true --browser.gatherUsageStats=false
