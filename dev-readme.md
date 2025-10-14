# Developer README

## Setting Up Local Environment

### Clone the Repository

Starting from scratch, go into a test folder and follow these steps to set up the code locally. This will clone the repository, switch to the desired branch, and set up the Python environment:

```bash
git clone https://github.com/tradinghours/tradinghours-python.git

cd tradinghours-python

python -m venv venv

venv\Scripts\activate  # on Windows
# or
source venv/bin/activate  # on Unix or MacOS

pip install -e .
```

You can now use the package from this directory.

### Running Tests

To run the tests, you need to install the development requirements (e.g., `pytest`):

```bash
pip install -e .[dev]

pytest
```

The library uses SQLite as the default database, which requires no additional setup.

### Configuring Data Sources

By default, the library downloads data from the TradingHours.com API (v4 endpoint). You can configure alternative data sources by creating a `tradinghours.ini` file:

```ini
[data]
source = file:///path/to/data.zip
# or
source = s3://bucket/path/to/data.zip
# or
source = https://example.com/data.zip
```

#### Supported Data Sources

1. **Default (v4 API)**: Leave `source` empty or unset
   - Automatically uses your API token
   - Efficient ETag-based change detection
   - Downloads latest data from TradingHours.com

2. **Local File**: `file:///absolute/path/to/data.zip`
   - Uses modification time (mtime) for change detection
   - Works cross-platform (Windows/Unix)
   - Useful for offline development or testing

3. **Custom HTTPS**: `https://example.com/data.zip`
   - Uses ETag or Last-Modified headers for change detection
   - Falls back to always downloading if headers unavailable

4. **S3**: `s3://bucket/key/data.zip` (requires boto3)
   - Install with: `pip install boto3`
   - Uses S3 ETag for change detection
   - Requires AWS credentials configured

#### Change Detection

The library automatically detects data changes using:
- **ETag** for HTTP/HTTPS and S3 sources
- **mtime** (modification time) for file:// sources
- Falls back to timestamp comparison if ETag unavailable

This ensures efficient updates - data is only downloaded when it has actually changed.

## Release Process

### Overview

The CI/CD process uses GitHub Actions to automate testing and releasing the project. The workflow includes several steps described below:

1. **Create a Pull Request (PR) against `pre-release`:**
   - This will trigger the `tests.yml` workflow.
   - If all tests pass, merge with the `pre-release` branch.

2. **PR against `main`:**
   - Increment the version number in `src\tradinghours\__init__.py`.
   - Describe the changes in `release_log.txt` under the `## new_release` heading. (But keep the heading as it is)
   - Open a PR from the `pre-release` branch to `main`.
   - This will trigger the `test_release.yml` workflow.
   - If the tests pass, merge with the `main` branch.

3. **Automatic Release:**
   - Merging with `main` triggers the `release.yml` workflow.
   - This will push to PyPI and create a release tag on GitHub.

4. **Post Release:**
   - If there were any changes to the server mode's schema:
     - run the server mode (`tradinghours serve`) and pull the openapi.json file.
     - In the docs.tradinghours.com repo, replace the public/th-python-server/openapi.json file with the new one.
     - Commit and push the changes to main.
   

## GitHub Actions Workflows

### `tests.yml`

This workflow runs tests across different configurations including coverage, database integration tests, and various OS and Python versions.

#### Trigger

The workflow is triggered on pull requests to the `pre-release` branch.

#### Sections

1. **Coverage**
2. **Database Tests**
3. **OS Versions and API Levels**
4. **Python Versions**

### `test_release.yml`

This workflow ensures that the package can be pushed and pulled from the test PyPI repository before an actual release.

#### Trigger

The workflow is triggered on pull requests to the `main` branch.

#### Steps

1. **Push to Test PyPI**:
    - Checks if the version has been incremented.
    - Releases the package to Test PyPI.
2. **Test from Test PyPI**:
    - Installs the package from Test PyPI.
    - Runs all tests to ensure the package works as expected.

### `release.yml`

This workflow publishes the package to PyPI and creates a release on GitHub.

#### Trigger

The workflow is triggered on push events to the `main` branch.

#### Steps

1. **Update Version and Summary**:
   - Sets the version and updates the release log.
2. **Build and Publish**:
   - Publishes the package to PyPI using Flit.
3. **Create GitHub Release**:
   - Creates a new GitHub release with the current version and summary.
