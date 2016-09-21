Authors (chronological)
=======================

-   [Mike Stringer](https://datascopeanalytics.com/team/mike-stringer/)
-   [Vlad Seghete](https://datascopeanalytics.com/team/vlad-seghete/)
-   [Yoke Peng
    Leong](https://datascopeanalytics.com/team/yoke-peng-leong/)

Contributing
============

Contributions are welcome, and they are greatly appreciated! Every
little bit helps, and credit will always be given. You can contribute in
many ways.

Design Philosophy
-----------------

-   "Simplicity is better than functionality." - Pieter Hintjens
-   "The API matters most, everything else is secondary." - Kenneth
    Reitz

Types of Contributions
----------------------

### Report Bugs

Report bugs at <https://github.com/datascopeanalytics/traces/issues>.

If you are reporting a bug, please include:

-   Your operating system name and version.
-   Any details about your local setup that might be helpful
    in troubleshooting.
-   Detailed steps to reproduce the bug.

### Fix Bugs

Look through the GitHub issues for bugs. Anything tagged with "bug" and
"help wanted" is open to whoever wants to implement it.

### Implement Features

Look through the GitHub issues for features. Anything tagged with
"enhancement" and "help wanted" is open to whoever wants to implement
it.

### Write Documentation

traces could always use more documentation, whether as part of the
official traces docs, in docstrings, or even on the web in blog posts,
articles, and such.

### Submit Feedback

The best way to send feedback is to file an issue at
<https://github.com/datascopeanalytics/traces/issues>.

If you are proposing a feature:

-   Explain in detail how it would work.
-   Keep the scope as narrow as possible, to make it easier
    to implement.
-   Remember that this is a volunteer-driven project, and that
    contributions are welcome :)

When you are suggesting an enhancement, please include specific use
cases that demonstrate why the proposed enhancement is useful and make
sure that the proposed enhancement is aligned with the goals of the
project.

Get Started!
------------

Ready to contribute? Here's how to set up `traces` for local
development.

1.  Fork the `traces` repo on GitHub.
2.  Clone your fork locally:

    ``` {.sourceCode .bash}
    $ git clone git@github.com:your_name_here/traces.git
    ```

3.  Install your local copy into a virtualenv. Assuming you have
    virtualenvwrapper installed, this is how you set up your fork for
    local development:

    ``` {.sourceCode .bash}
    $ mkvirtualenv traces
    $ cd traces/
    $ python setup.py develop
    ```

4.  Create a branch for local development:

    ``` {.sourceCode .bash}
    $ git checkout -b name-of-your-bugfix-or-feature
    ```

Now you can make your changes locally.

5.  When you're done making changes, check that your changes pass flake8
    and the tests, including testing other Python versions with tox:

        .. code:: bash

    > \$ flake8 traces tests \$ python setup.py test or py.test \$ tox

To get flake8 and tox, just pip install them into your virtualenv.

6.  Commit your changes and push your branch to GitHub:

    ``` {.sourceCode .bash}
    $ git add .
    $ git commit -m "Your detailed description of your changes."
    $ git push origin name-of-your-bugfix-or-feature
    ```

7.  Submit a pull request through the GitHub website.

Pull Request Guidelines
-----------------------

Pull requests are welcome! If the pull request is in response to an
existing Bug Report or Enhancement Request, please refer to it in the
description. Otherwise, if the pull request is a bug fix then make sure
to describe the bug just like if it were a bug report issue. If it's an
enhancement, describe the uses cases like you would when creating an
enhancement request.

Before you submit a pull request, check that it meets these guidelines:

1.  The pull request should include tests.
2.  If the pull request adds functionality, the docs should be updated.
    Put your new functionality into a function with a docstring, and add
    the feature to the list in README.rst.
3.  The pull request should work for Python 2.7, 3.4 and 3.5, and
    for PyPy. Check <https://circleci.com/gh/datascopeanalytics/traces>
    and make sure that the tests pass for all supported Python versions.

Tips
----

To run a subset of tests:

    $ python -m unittest tests.test_traces
