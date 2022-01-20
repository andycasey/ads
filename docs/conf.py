# Configuration file for the Sphinx documentation builder.
#
# Full list of options can be found in the Sphinx documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys

# add the demo python code to the path, so that it can be used to demonstrate
# source links
#import ads

#
# -- Project information -----------------------------------------------------
#

project = "ads"
copyright = "2016-2020"
author = "Andy Casey and others"

#
# -- General configuration ---------------------------------------------------
#

extensions = [
    # Sphinx's own extensions
    "sphinx.ext.autodoc",
    "sphinx.ext.extlinks",
    "sphinx.ext.intersphinx",
    "sphinx.ext.autosummary",
    "sphinx.ext.mathjax",
    "sphinx.ext.todo",
    "sphinx.ext.viewcode",
    # Our custom extension, only meant for Furo's own documentation.
    # External stuff
    "myst_parser",
    "sphinx_copybutton",
    "sphinx_design",
    "sphinx_inline_tabs",
]
autodoc_default_flags = ["members"]
autosummary_generate = True
autodoc_default_options = {
    "members": True,
    "member-order": "bysource",
    "special-members": "__init__"
}
templates_path = ["_templates"]

#
# -- Options for extlinks ----------------------------------------------------
#
extlinks = {
    "pypi": ("https://pypi.org/project/%s/", ""),
}

#
# -- Options for intersphinx -------------------------------------------------
#
intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "sphinx": ("https://www.sphinx-doc.org/en/master", None),
}

#
# -- Options for TODOs -------------------------------------------------------
#
todo_include_todos = True

#
# -- Options for Markdown files ----------------------------------------------
#
myst_enable_extensions = [
    "colon_fence",
    "deflist",
]
myst_heading_anchors = 3

#
# -- Options for HTML output -------------------------------------------------
#

html_theme = "furo"
html_title = "&nbsp;"
language = "en"

html_static_path = ["_static"]
html_logo = "_static/ads-logo-square.png"
#html_theme_options = {
#    "light_logo": "ads-logo-light-square.png",
#    "dark_logo": "ads-logo-square.png"
#}
html_css_files = ["pied-piper-admonition.css"]
html_theme_options = {
    "announcement": (
        "If things look broken, try disabling your ad-blocker. "
        "It's because 'ads' seems a lot like <b>ad</b>(<i>vertisement</i>)<b>s</b>, "
        "and there's not much I can do about that!"
    )
}
