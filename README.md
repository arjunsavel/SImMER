# SImMER
[![Build Status](https://dev.azure.com/asavel/SImMER/_apis/build/status/arjunsavel.SImMER?branchName=master)](https://dev.azure.com/asavel/SImMER/_build?definitionId=1&_a=summary) [![codecov](https://codecov.io/gh/arjunsavel/simmer/branch/master/graph/badge.svg?token=5ERhXGwSDo)](https://codecov.io/gh/arjunsavel/simmer) [![Code Climate](https://img.shields.io/codeclimate/maintainability/arjunsavel/SImMER?style=flat)](https://codeclimate.com/github/arjunsavel/SImMER) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Build Status](https://readthedocs.org/projects/simmer/badge/?version=latest)](http://simmer.readthedocs.io/en/latest/?badge=latest) [![PyPI version](https://badge.fury.io/py/simmer.svg)](https://badge.fury.io/py/simmer) [![Conda Version](https://img.shields.io/conda/v/conda-forge/simmer?color=g&label=conda-forge%20%20%20%20%20&logo=conda-forge)](https://anaconda.org/conda-forge/simmer)


Repository for developing the ```SImMER``` image reduction pipeline. If you'd like to help out, take a look at our [ways to contribute](https://github.com/arjunsavel/simmer/blob/master/CONTRIBUTING.md).

<p align="center">
  <img src="https://github.com/arjunsavel/SImMER/blob/master/docs/img/final_image.png" />
</p>


## Installation
To install with conda (the recommended method), run
```
conda config --add channels conda-forge
conda install simmer
```
To install with pip, run
```
pip install simmer
```
Or, to install from source, run
```
python3 -m pip install -U pip
python3 -m pip install -U setuptools setuptools_scm pep517
git clone https://github.com/arjunsavel/SImMER.git
cd simmer
python3 -m pip install -e .
```
## Documentation
To get started, read the docs at [our readthedocs site](https://simmer.readthedocs.io/en/latest/pages/about/).
