# SImMER
[![arXiv](https://img.shields.io/badge/arXiv-2212.00641-b31b1b.svg)](https://arxiv.org/abs/2212.00641)
 [![Tests](https://github.com/arjunsavel/SImMER/actions/workflows/run_tests.yml/badge.svg)](https://github.com/arjunsavel/SImMER/actions/workflows/run_tests.yml)
[![codecov](https://codecov.io/gh/arjunsavel/simmer/branch/main/graph/badge.svg?token=eMUOVt99Gh)](https://codecov.io/gh/arjunsavel/simmer) [![Maintainability](https://api.codeclimate.com/v1/badges/d1fa9d77e8fbcc96619a/maintainability)](https://codeclimate.com/github/arjunsavel/SImMER/maintainability) [![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Build Status](https://readthedocs.org/projects/simmer/badge/?version=latest)](http://simmer.readthedocs.io/en/latest/?badge=latest) [![PyPI version](https://badge.fury.io/py/simmer.svg)](https://badge.fury.io/py/simmer) [![Conda Version](https://img.shields.io/conda/v/conda-forge/simmer?color=g&label=conda-forge%20%20%20%20%20&logo=conda-forge)](https://anaconda.org/conda-forge/simmer) [![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black) [![Yaml Lint](https://github.com/arjunsavel/SImMER/actions/workflows/yaml.yml/badge.svg)](https://github.com/arjunsavel/SImMER/actions/workflows/yaml.yml)



Repository for developing the ```SImMER``` image reduction pipeline. If you'd like to help out, take a look at our [ways to contribute](https://github.com/arjunsavel/simmer/blob/main/CONTRIBUTING.md). If you use this package in your research, please cite [our paper](https://iopscience.iop.org/article/10.1088/1538-3873/aca4f9/meta?casa_token=GQzZtqAVVDAAAAAA:uyvTw9R2VIWITJcGAioptUSJFmGMFaj4kS61ZGKKRf2k97nHVv5libuIly2FFBR95Iiq0576P2t90Hw5KqyFYehRcbsx).

<p align="center">
  <img src="https://github.com/arjunsavel/SImMER/blob/main/docs/img/final_image.png" />
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
