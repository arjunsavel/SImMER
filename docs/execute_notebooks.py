from glob import glob

import nbformat
from nbconvert.preprocessors import ExecutePreprocessor

for notebook_filename in glob("pages/*.ipynb"):
    with open(notebook_filename) as f:
        nb = nbformat.read(f, as_version=4)

    ep = ExecutePreprocessor(timeout=600, kernel_name="python3")
    ep.preprocess(nb, {"metadata": {"path": "pages/"}})

    with open(notebook_filename, "w", encoding="utf-8") as f:
        nbformat.write(nb, f)
