Integrations
----------------
As a growing open-source project, :code:`SImMER` has made use of a number of freely
available integrations and services, which are summarized below:

- `GitHub Actions <https://github.com/features/actions>`_: With these automated
  checks, inconsistent commits will be flagged as such. A number of the below
  services are implemented as GitHub Actions, which manifest as
  `checks <https://developer.github.com/v3/checks/>`_ on different commits. In
  general, we would like all of our checks to pass before pull requests are
  merged. Configuration files for GitHub Actions are contained in
  :code:`.github/workflows`.

- `Azure Pipelines <https://azure.microsoft.com/en-us/services/devops/pipelines/>`_:
  the main
  `continuous integration service <https://help.github.com/en/actions/building-and-testing-code-with-continuous-integration/about-continuous-integration>`_
  that we use. The benefit of this
  service for :code:`SImMER` is that testing on virtual Window machines is possible ---
  which is desirable for Windows users who may use our code. The configuration
  file for this service is :code:`azure-pipelines.yml`.

- `black <https://black.readthedocs.io/en/stable/>`_: a Python code-formatter.
  It generally conforms to `PEP-8 <https://www.python.org/dev/peps/pep-0008/>`_
  standards, but it does so in a very deterministic manner, which is helpful for
  our code. The basic pre-commit configuration is location in :code:`.pre-commit-config.yaml`,
  while more detailed configuration is detailed in :code:`pyproject.toml`. black is also
  implemented as a GitHub action, with the relevant configuration in
  :code:`.github/workflows/style`. To apply the same methodology to our Jupyter
  notebooks, we also make use of
  `black_nbconvert <https://github.com/dfm/black_nbconvert>`_.

- `isort <https://isort.readthedocs.io/en/latest/>`_: a tool for sorting imports
  in Python files. As with black, the basic pre-commit configuration is location
  in :code:`.pre-commit-config.yaml`, while more detailed configuration is detailed in
  :code:`pyproject.toml`. black is also implemented as a GitHub action, with the
  relevant configuration in :code:`.github/workflows/style`.

- `pre-commit hooks <https://pre-commit.com/>`_: these can be applied to any
  local commits. The associated configuration file is :code:`.pre-commit-config.yml`.

- `yamllint <https://github.com/adrienverge/yamllint>`_: lints our YAML files,
  checking them for bugs, syntax errors, and general style. The associated
  configuration file is :code:`.yamllint`. Implemented as a GitHub check and pre-commit
  hook.

- `Sphinx <https://www.sphinx-doc.org/en/master/>`_: the code that we use to build
  our documentation. All documentation is held in `docs/`, with configuration in
  :code:`docs/source/conf.py`.

- `Dependabot <https://dependabot.com/>`_: automatically checks whether
  dependencies are kept up-to-date. Configuration is held in :code:`.github/dependabot.yml`.

- `Codecov <https://codecov.io/gh>`_: checks what percentage of our code base
  is covered in our automated tests. Ideally, we'd like to keep our coverage above
  95% if it is in a production environment. Relevant configurations are noted in
  :code:`codecov.yml`.

- `ReadTheDocs <https://readthedocs.org/>`_: the service on which :code:`SImMER` hosts
  its documentation. Builds are run on every commit to the :code:`master` branch.
  Configuration is stored in the :code:`readthedocs.yml` file.
