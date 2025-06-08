# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = 'ATA_V2'
copyright = '2025, Your Name'
author = 'Your Name'

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

import os
import sys
import shutil
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx_autodoc_typehints',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

def setup(app):
    def copy_diagram(app):
        target_dir = os.path.join(app.outdir, '_static', 'diagrams')
        os.makedirs(target_dir, exist_ok=True)
        shutil.copy(
            os.path.abspath(os.path.join(os.path.dirname(__file__), '../../src/tests/run_test.drawio.html')),
            os.path.join(target_dir, 'run_test.drawio.html')
        )
    app.connect('builder-inited', copy_diagram)

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = 'sphinx_rtd_theme'
html_static_path = ['_static']
