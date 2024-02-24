# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "digital-experiments"
copyright = "2023, John Gardner"
author = "John Gardner"
release = "2.0.4"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.duration",
    "sphinx.ext.autodoc",
    "sphinx.ext.autosummary",
    "nbsphinx",
    "sphinx.ext.mathjax",
    "sphinx.ext.napoleon",
    "sphinx.ext.intersphinx",
    "sphinxext.opengraph",
    "sphinx_design",
    "sphinx_codeautolink",
    "sphinx_copybutton",
]

templates_path = ["_templates"]
exclude_patterns = []

intersphinx_mapping = {
    "python": ("http://docs.python.org/", None),
    "pandas": ("https://pandas.pydata.org/docs/", None),
}
html_theme = "furo"
# html_static_path = ["_static"]
autodoc_member_order = "bysource"

copybutton_prompt_text = (
    r">>> |\.\.\. |\$ |In \[\d*\]: | {2,5}\.\.\.: | {5,8}: "
)
copybutton_prompt_is_regexp = True
nbsphinx_execute_arguments = [
    "--InlineBackend.figure_formats={'svg'}",
]
copybutton_selector = "div.copy-button pre"

logo_highlight_colour = "#3c78d8"
code_color = "#3c78d8"
html_theme_options = {
    "sidebar_hide_name": True,
    "light_css_variables": {
        "color-problematic": code_color,
        "color-brand-primary": logo_highlight_colour,
        "color-brand-content": logo_highlight_colour,
    },
    "dark_css_variables": {
        "color-problematic": code_color,
    },
}

html_logo = "logo-square.svg"
html_title = "digital-experiments"


# override the default css to match the furo theme
nbsphinx_prolog = """
.. raw:: html

    <style>
        .jp-RenderedHTMLCommon tbody tr:nth-child(odd),
        div.rendered_html tbody tr:nth-child(odd) {
            background: var(--color-code-background);
        }
        .jp-RenderedHTMLCommon tr,
        .jp-RenderedHTMLCommon th,
        .jp-RenderedHTMLCommon td,
        div.rendered_html tr,
        div.rendered_html th,
        div.rendered_html td {
            color: var(--color-content-foreground);
        }
        .jp-RenderedHTMLCommon tbody tr:hover,
        div.rendered_html tbody tr:hover {
            background: #3c78d8aa;
        }
        div.nbinput.container div.input_area {
            /* border radius of 10px, but no outline */
            border-radius: 10px;
            border-style: none;
        }
        div.nbinput.container div.input_area > div.highlight > pre {
            padding: 10px;
            border-radius: 10px;
        }

    </style>
"""
nbsphinx_prompt_width = "0"
