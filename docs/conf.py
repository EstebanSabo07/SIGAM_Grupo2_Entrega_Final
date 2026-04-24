"""Sphinx configuration for SIGAM documentation."""

from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

project = "SIGAM"
author = "LEAD University / CGR Costa Rica"
release = "2025"
language = "es"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.githubpages",
]

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "furo"
html_title = "SIGAM"
html_logo = "../assets/logo_lead.png"
html_static_path = ["_static"]
html_css_files = ["custom.css"]
html_baseurl = "https://estebansabo07.github.io/SIGAM_Grupo2_Entrega_Final/"
html_copy_source = False
html_show_sourcelink = False
html_theme_options = {
    "sidebar_hide_name": False,
    "light_css_variables": {
        "color-brand-primary": "#1A3A6B",
        "color-brand-content": "#1A3A6B",
        "color-api-name": "#1A3A6B",
        "color-api-pre-name": "#4A5568",
    },
    "dark_css_variables": {
        "color-brand-primary": "#8FC5FF",
        "color-brand-content": "#8FC5FF",
        "color-api-name": "#8FC5FF",
        "color-api-pre-name": "#D8DEE9",
    },
}

autodoc_member_order = "bysource"
autodoc_typehints = "description"
autosummary_generate = True

napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = False
napoleon_include_private_with_doc = True
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_use_ivar = True

autodoc_mock_imports = [
    "streamlit",
    "pandas",
    "plotly",
    "numpy",
    "sklearn",
    "sqlalchemy",
    "openpyxl",
    "pyrebase",
    "pyrebase4",
    "requests",
    "firebase_admin",
]
