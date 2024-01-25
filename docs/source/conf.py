# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "DGIpy"
copyright = "2024, Wagner Lab"
author = "Wagner Lab"
html_title = "DGIpy"

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

extensions = [
    "sphinx.ext.autodoc",
    "sphinx_autodoc_typehints",
    "sphinx.ext.linkcode",
    "sphinx_copybutton",
    "sphinx_github_changelog",
]

templates_path = ["_templates"]
exclude_patterns = []

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_static_path = []
html_css_files = [
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/fontawesome.min.css",
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/solid.min.css",
    "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/brands.min.css",
]
html_theme_options = {
    "footer_icons": [
        {
            "name": "GitHub",
            "url": "https://github.com/genomicmedlab/dgipy",
            "html": "",
            "class": "fa-brands fa-solid fa-github",
        },
        {
            "name": "Wagner Lab",
            "url": "https://www.nationwidechildrens.org/specialties/institute-for-genomic-medicine/research-labs/wagner-lab",
            "html": "",
            "class": "fa-solid fa-house",
        }
    ],
}
# -- autodoc things ----------------------------------------------------------
import os  # noqa: E402
import sys  # noqa: E402

sys.path.insert(0, os.path.abspath("../../dgipy"))
autodoc_preserve_defaults = True

# -- get version -------------------------------------------------------------
from importlib.metadata import version

release = version = version("dgipy")

# -- linkcode ----------------------------------------------------------------
def linkcode_resolve(domain, info):
    if domain != "py":
        return None
    if not info["module"]:
        return None
    filename = info["module"].replace(".", "/")
    return f"https://github.com/genomicmedlab/dgipy/blob/main/{filename}.py"


# -- code block style --------------------------------------------------------
pygments_style = "default"
pygements_dark_style = "monokai"
