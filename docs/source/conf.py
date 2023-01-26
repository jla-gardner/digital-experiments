import os
import shutil
import sys
from pathlib import Path

SOURCE_DIR = Path(__file__).parent
PROJECT_ROOT = SOURCE_DIR.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Copy examples to source directory
examples_source = PROJECT_ROOT / "examples"
examples_dest = SOURCE_DIR / "examples"
if examples_dest.exists():
    shutil.rmtree(examples_dest)
os.mkdir(examples_dest)

for file in examples_source.glob("*.ipynb"):
    shutil.copy(file, examples_dest / file.name)


# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "digital-experiments"
copyright = "2023, John Gardner"
author = "John Gardner"
release = "0.1.9"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.duration",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "nbsphinx",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
]

templates_path = ["_templates"]
exclude_patterns = []

html_css_files = [
    "css/linebreaks.css",
]

intersphinx_mapping = {
    "python": ("http://docs.python.org/", None),
    "pandas": ("http://pandas.pydata.org/pandas-docs/dev", None),
}

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_static_path = ["_static"]
