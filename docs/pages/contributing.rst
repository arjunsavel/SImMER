Contributing
=============
Firstly — thanks so much for your interest in contributing to :code:`SImMER`!
We look forward to any additions you might make.

If you're new to the Git workflow, please first familiarize yourself with the
`Astropy <https://docs.astropy.org/en/stable/development/workflow/development_workflow.html>`_
workflow.

A few items that are specific to our project:

- Please submit a pull request as soon as you feel comfortable! It's entirely
  fine if your code isn't finalized; you could submit a
  `draft <https://github.blog/2019-02-14-introducing-draft-pull-requests/>`_,
  which would allow us to provide our thoughts on your feature even while it's
  in progress.

- Consider downloading `pre-commit <https://pre-commit.com/>`_ before you make
  new commits; this will make it much easier for you to ensure that your code
  passes all relevant checks.

- If you add a new module (i.e., add a new file with Python code within
  :code:`src/simmer`), you'll need to add its name as a string to the
  :code:`known_third_party` list at the bottom of `pyproject.toml`; otherwise,
  the sorting check that is performed won't recognize your new module, and it
  will throw an error.

- Be sure to write tests for your new code!

- To run tests from a single file, run :code:`python -m src.simmer.tests.new_file`
  from the root directory (that is, the outermost :code:`SImMER` directory if
  you've clones from GitHub).
