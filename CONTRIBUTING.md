# Contributing to Pylogic

The following is a set of guidelines for contributing to `pylogic`. These are mostly guidelines, however there are some special steps you need to be aware of when creating a pull request so we end up with a standardized code. Please feel free to propose changes to this document by submitting an issue.

## Technicalities

Installing `pyenv` is recommended if you'd like to manage multiple python versions. But you are free to choose how to manage your environment. I would still recommend using a virtual environment with at least python `3.8.10`.

Once you have your environment with `python>=3.8`, install the `test_requirements.txt` by running `pip install -r test_requirements.txt`. We use `pre-commit` hooks so we maintain an standardized code and for linting purposes. Thus, you must also run `pre-commit install`. Github actions have been set on commits and on pull requests, so make sure that you installed the pre-commits and that all hooks pass.

## Running Test Suite

To run the test suite just use execute:

```
tox
```

You should see an output like the following:

```
collected 5 items

tests/test_propositional.py::test_to_cnf PASSED                         [ 20%]
tests/test_propositional.py::test_cnf_class PASSED                      [ 40%]
tests/test_propositional.py::test_pl_kb PASSED                          [ 60%]
tests/test_propositional.py::test_cnf_parser PASSED                     [ 80%]
tests/test_propositional.py::test_pl_resolution PASSED                  [100%]

---------- coverage: platform linux, python 3.8.10-final-0 -----------
Coverage XML written to file coverage.xml
```

We are currently aiming for a coverage `>85%` and this threshold could be incremented. So, for hygiene purposes is ideal creating tests for the code you'd like to deploy.

## Docs Testing

TBD. Not yet decided which documentation approach to take (restructuredText and inline documentation) or other form of documentation.
