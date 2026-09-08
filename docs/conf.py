"""Sphinx configuration for cafein.lca."""

import cafein.lca

project = "cafein.lca"
author = "Henrikki Tenkanen"
copyright = "2026, Henrikki Tenkanen"
version = release = cafein.lca.__version__

extensions = [
    "myst_nb",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "sphinx_design",
]

autosummary_generate = True
napoleon_google_docstring = False
napoleon_numpy_docstring = True

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "pandas": ("https://pandas.pydata.org/docs", None),
}

nb_execution_mode = "auto"
nb_execution_timeout = 120

html_theme = "sphinx_book_theme"
html_title = "cafein.lca"
html_theme_options = {
    "repository_url": "https://github.com/cafein-py/cafein.lca",
    "use_repository_button": True,
}

exclude_patterns = ["_build", "workbook-audit.md"]
