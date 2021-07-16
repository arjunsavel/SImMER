Versioning
===========

Philosophy
-----------
:code:`SImMER` generally follows `semantic versioning <https://semver.org/>`_
guidelines. In brief, this means that our version numbers follow a `AA.BB.CC`
convenion, with `AA` incrementing when a large, backward-incompatible changes
are introduced to the code base; `BB` incrementing when backward-compatible
functionality is added to a code; and `CC` incrementing whenever backward-compatible 
bugs are fixed. For example:

- If a user input of square root scaling resulted in quadratic scaling, fixing
  this would result in `CC` increasing
- If new plotting arguments are added to the plotting schema, `BB would increase
- If :code:`Instruments` were deprecated and a new class :code:`Telescopes` were
  used in its stead, `AA` would increase

Additionally, suffixes (e.g. "-beta" or "-dev") may be added to the release tag,
signifying the degree to which developers are confident in production-ready
(i.e., bug-free) code.


In practice
------------
This only applies to developers with write access to the code base. All that
needs to be done is:

1. Adjust the version specified in :code:`src/simmer/__init__.py`. This will
   automatically update docs and :code:`setup.py` configurations.
2. Update the GitHub release version to match the version specified in Step 1.
   This will automatically publish the build on PyPI.
3. Wait for the `autotick bot <https://justcalamari.github.io/jekyll/update/2018/06/11/introduction.html>`_ on the `SImMER feedstock repository <https://github.com/conda-forge/simmer-feedstock>`_ to make a PR updating the version number. Then, wait for all the tests to pass.
4. Make any neessary dependency changes to the corresponding recipe, then merge the PR. *Note*: Don't add [skip ci] to the merge commit in the feedstock repository! This suffix will skip all continuous integration run in that repository, not just the SImMER tests on Azure. Therefore, the newest version won't be available to install on conda.
