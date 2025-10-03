This readme covers the Github Actions workflows that manage the automated test and release process. These workflows I will be referring to are located in the .github/workflows folder.

There are 3 steps involved to go from a development branch, which can have any name to the main branch, which automatically results in the release of the package.

1. Pull Request against the `pre-release` branch:
   Immediately when this PR is created, so before it is merged, the tests.yml workflow runs. This ensures that all tests pass before merging code into the `pre-release` branch.

2. Pull Request against the `main` branch:
   Immediately when this PR is created, so before it is merged, the test_release.yml workflow runs. This ensures that the code can be built and pushed to pypi successfully and that the code that is pushed still passes all tests after it is downloaded.

3. Merge into the `main` branch:
   When the merge is completed, the release.yml workflow runs.

Before PR against `main`:
 * __init__.__version__ must be incremented
 * release_log.txt needs to be updated
   * the new release section should get the header: '## new_release', release.yml looks for that.


## tests.yml
 This workflow covers three jobs:

 1. Run the tests with coverage tracking
 2. Run the tests with all combinations of different operating systems, and API key access levels
 3. Run the tests with different python versions


## test_release.yml
 This workflow covers two jobs:

 1. Push the code from pre-release to test.pypi.org
 2. Install the code from test.pypi.org and run the tests with that code.


## release.yml
 This workflow covers one job:

 1. It makes the release to pypi.org
