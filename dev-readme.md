## Setup

* clone the repository
* create virtual environment and activate it
* run: `pip install -e .[dev]`, which installs with dev dependencies
* or run: `pip install -e .`, which only installs regular dependencies
* run pytest, after importing tradinghours data



## CI/CD

* from whatever branch you are working on, open a PR against `pre-release`
  * this will trigger the tests.yml workflow
  * if these pass, merge with `pre-release`

* When `pre-release` contains everything for the new release, open a PR against `main`
  * this will trigger the test_release.yml workflow
  * if that passes, merge with `main`

* Merging with main triggers the release.yml workflow
  * this will push to pypi and create a release tag on github