.. _contrib:

==================
How to contribute?
==================

Contributions of any size are greatly appreciated! You can
make a significant impact on UltraPlot by just using it and
reporting `issues <https://github.com/ultraplot/ultraplot/issues>`__.

The following sections cover some general guidelines
regarding UltraPlot development for new contributors. Feel
free to suggest improvements or changes to this workflow.

.. _contrib_features:

Feature requests
================

We are eager to hear your requests for new features and
suggestions regarding the current API. You can submit these as
`issues <https://github.com/ultraplot/ultraplot/issues/new>`__ on Github.
Please make sure to explain in detail how the feature should work and keep the scope as
narrow as possible. This will make it easier to implement in small pull requests.

If you are feeling inspired, feel free to add the feature yourself and
submit a pull request!

.. _contrib_bugs:

Report bugs
===========

Bugs should be reported using the Github
`issues <https://github.com/ultraplot/ultraplot/issues>`__ page. When reporting a
bug, please follow the template message and include copy-pasteable code that
reproduces the issue. This is critical for contributors to fix the bug quickly.

If you can figure out how to fix the bug yourself, feel free to submit
a pull request.

.. _contrib_tets:

Write tests
===========

Most modern python packages have ``test_*.py`` scripts that are run by `pytest`
via continuous integration services like `Travis <https://travis-ci.com>`__
whenever commits are pushed to the repository. Currently, UltraPlot's continuous
integration includes only the examples that appear on the website User Guide (see
`.travis.yml`), and `Casper van Elteren <https://github.com/cvanelteren>` runs additional tests
manually. This approach leaves out many use cases and leaves the project more
vulnerable to bugs. Improving ultraplot's continuous integration using `pytest`
and `pytest-mpl` is a *critical* item on our to-do list.

If you can think of a useful test for ultraplot, feel free to submit a pull request.
Your test will be used in the future.

.. _contrib_docs:

Write documentation
===================

Documentation can always be improved. For minor changes, you can edit docstrings and
documentation files directly in the GitHub web interface without using a local copy.

* The docstrings are written in
  `reStructuredText <http://docutils.sourceforge.net/docs/user/rst/quickref.html>`__
  with `numpydoc <https://numpydoc.readthedocs.io/en/latest/>`__ style headers.
  They are embedded in the :ref:`API reference` section using a
  `fork of sphinx-automodapi <https://github.com/lukelbd/sphinx-automodapi>`__.
* Other sections are written using ``.rst`` files and ``.py`` files in the ``docs``
  folder. The ``.py`` files are translated to python notebooks via
  `jupytext <https://jupytext.readthedocs.io/en/latest/>`__ then embedded in
  the User Guide using `nbsphinx <https://nbsphinx.readthedocs.io/en/0.5.0/>`__.
* The `default ReST role <https://www.sphinx-doc.org/en/master/usage/configuration.html#confval-default_role>`__
  is ``py:obj``. Please include ``py:obj`` links whenever discussing particular
  functions or classes -- for example, if you are discussing the
  :func:`~ultraplot.axes.Axes.format` method, please write
  ```:func:`~ultraplot.axes.Axes.format` ``` rather than ``format``. ultraplot also uses
  `intersphinx <http://www.sphinx-doc.org/en/stable/ext/intersphinx.html>`__
  so you can link to external packages like matplotlib and cartopy.

To build the documentation locally, use the following commands:

.. code:: bash

   cd docs
   # Install dependencies to the base conda environment..
   conda env update -f environment.yml
   # ...or create a new conda environment
   # conda env create -n ultraplot-dev --file docs/environment.yml
   # source activate ultraplot-dev
   # Create HTML documentation
   make html

The built documentation should be available in ``docs/_build/html``.

.. _contrib_pr:

Preparing pull requests
=======================

New features and bug fixes should be addressed using pull requests.
Here is a quick guide for submitting pull requests:

#. Fork the
   `ultraplot GitHub repository <https://github.com/ultraplot/ultraplot>`__.  It's
   fine to keep "ultraplot" as the fork repository name because it will live
   under your account.

#. Clone your fork locally using `git <https://git-scm.com/>`__, connect your
   repository to the upstream (main project), and create a branch as follows:

   .. code-block:: bash

      git clone git@github.com:YOUR_GITHUB_USERNAME/ultraplot.git
      cd ultraplot
      git remote add upstream git@github.com:ultraplot/ultraplot.git
      git checkout -b your-branch-name master

   If you need some help with git, follow the
   `quick start guide <https://git.wiki.kernel.org/index.php/QuickStart>`__.

#. Make an editable install of ultraplot by running:

   .. code-block:: bash

      pip install -e .

   This way ``import ultraplot`` imports your local copy,
   rather than the stable version you last downloaded from PyPi.
   You can ``import ultraplot; print(ultraplot.__file__)`` to verify your
   local copy has been imported.

#. Install `pre-commit <https://pre-commit.com>`__ and its hook on the
   ``ultraplot`` repo as follows:

   .. code-block:: bash

      pip install --user pre-commit
      pre-commit install

   Afterwards ``pre-commit`` will run whenever you commit.
   `pre-commit <https://pre-commit.com/>`__ is a framework for managing and
   maintaining multi-language pre-commit hooks to
   ensure code-style and code formatting is consistent.

#. You can now edit your local working copy as necessary. Please follow
   the `PEP8 style guide <https://www.python.org/dev/peps/pep-0008/>`__.
   and try to generally adhere to the
   `black <https://black.readthedocs.io/en/stable/>`__ subset of the PEP8 style
   (we may automatically enforce the "black" style in the future).
   When committing, ``pre-commit`` will modify the files as needed,
   or will generally be clear about what you need to do to pass the pre-commit test.

   Please break your edits up into reasonably sized commits:


   .. code-block:: bash

      git commit -a -m "<commit message>"
      git push -u

   The commit messages should be short, sweet, and use the imperative mood,
   e.g. "Fix bug" instead of "Fixed bug".

   ..
      #. Run all the tests. Now running tests is as simple as issuing this command:
         .. code-block:: bash
            coverage run --source ultraplot -m py.test
         This command will run tests via the ``pytest`` tool against Python 3.7.

#. If you intend to make changes or add examples to the user guide, you may want to
   open the ``docs/*.py`` files as
   `jupyter notebooks <https://jupyter-notebook.readthedocs.io/en/stable/>`__.
   This can be done by
   `installing jupytext <https://jupytext.readthedocs.io/en/latest/install.html>`__,
   starting a jupyter session, and opening the ``.py`` files from the ``Files`` page.

#. When you're finished, create a new changelog entry in ``CHANGELOG.rst``.
   The entry should be entered as:

   .. code-block::

      * <description> (:pr:`<PR number>`) by `<author name>`_.

   where ``<description>`` is the description of the PR related to the change,
   ``<PR number>`` is the pull request number, and ``<author name>`` is your first
   and last name. Make sure to add yourself to the list of authors at the end of
   ``CHANGELOG.rst`` and the list of contributors in ``docs/authors.rst``.
   Also make sure to add the changelog entry under one of the valid
   ``.. rubric:: <heading>`` headings listed at the top of ``CHANGELOG.rst``.

#. Finally, submit a pull request through the GitHub website using this data:

   .. code-block::

      head-fork: YOUR_GITHUB_USERNAME/ultraplot
      compare: your-branch-name

      base-fork: ultraplot/ultraplot
      base: master

Note that you can create the pull request before you're finished with your
feature addition or bug fix. The PR will update as you add more commits. UltraPlot
developers and contributors can then review your code and offer suggestions.

.. _contrib_release:

Release procedure
=================
Ultraplot follows EffVer (`Effectual Versioning <https://jacobtomlinson.dev/effver/>`_). Changes to the version number ``X.Y.Z`` will reflect the effect on users: the major version ``X`` will be incremented for changes that require user attention (like breaking changes), the minor version ``Y`` will be incremented for safe feature additions, and the patch number ``Z`` will be incremented for changes users can safely ignore.

While version 1.0 has been released, we are still in the process of ensuring proplot is fully replaced by ultraplot as we continue development under the ultraplot name. During this transition, the versioning scheme reflects both our commitment to stable APIs and the ongoing work to complete this transition. The minor version number is incremented when changes require user attention (like deprecations or style changes), and the patch number is incremented for additions and fixes that users can safely adopt.

For now, `Casper van Eltern <https://github.com/cvanelteren>`__ is the only one who can
publish releases on PyPi, but this will change in the future. Releases should
be carried out as follows:

#. Create a new branch ``release-vX.Y.Z`` with the version for the release.

#. Make sure to update ``CHANGELOG.rst`` and that all new changes are reflected
   in the documentation:

   .. code-block:: bash

      git add CHANGELOG.rst
      git commit -m 'Update changelog'

#. Open a new pull request for this branch targeting ``master``.

#. After all tests pass and the pull request has been approved, merge into
   ``master``.

#. Get the latest version of the master branch:

   .. code-block:: bash

      git checkout master
      git pull

#. Tag the current commit and push to github:

   .. code-block:: bash

      git tag -a vX.Y.Z -m "Version X.Y.Z"
      git push origin master --tags

#. Build and publish release on PyPI:

   .. code-block:: bash

      # Remove previous build products and build the package
      rm -r dist build *.egg-info
      python setup.py sdist bdist_wheel
      # Check the source and upload to the test repository
      twine check dist/*
      twine upload --repository-url https://test.pypi.org/legacy/ dist/*
      # Go to https://test.pypi.org/project/ultraplot/ and make sure everything looks ok
      # Then make sure the package is installable
      pip install --index-url https://test.pypi.org/simple/ ultraplot
      # Register and push to pypi
      twine upload dist/*
