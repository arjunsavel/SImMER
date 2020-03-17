Installation
============

SImMER is meant to be a well-tested code across multiple operating systems. However, Windows testing is yet to be implemented, so installation may be especially buggy for Windows users.

.. note:: SImMER is currently a private, beta code. If you would like access, please contact Arjun Savel at asavel@berkeley.edu.


Installing from source
-----------------------

SImMER is developed on `GitHub <https://github.com/arjunsavel/shane-reduction>`_. If you received the code as a tarball or zip, skip to below the git clone line.

.. code-block:: bash

    python3 -m pip install -U pip
    python3 -m pip install -U setuptools setuptools_scm pep517
    git clone https://github.com/arjunsavel/shane-reduction.git
    cd shane-reduction
    python3 -m pip install -e .


Test the installation
---------------------

To ensure that the installation has been performed smoothly, feel free to run the unit and integration tests included with the package. The entire test suite should take on the order of 10 minutes to run. Before running the test suite, ensure that, in the :code:`aodirs.py` file, the :code:`raw_dir` and :code:`reddir` functions return the directory containing :code:`/src/simmer/tests/PHARO_integration/`. Make sure that the :code:`config` function returns the path to the config file in the :code:`shane-reduction` directory. From the shane-reduction directory, then run

.. code-block:: bash

    python3 -m unittest discover src
