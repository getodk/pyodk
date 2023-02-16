# pyODK
[![pypi](https://img.shields.io/pypi/v/pyodk.svg)](https://pypi.python.org/pypi/pyodk)

An API client for the [ODK Central API](https://odkcentral.docs.apiary.io). Use it to interact with your data and automate common tasks from Python.

This library aims to make common data analysis and workflow automation tasks as simple as possible by providing clear method names, types, and examples. It also provides convenient access to the full API using [HTTP verb methods](#raw-http-requests).


# Install

The currently supported Python version for `pyodk` is 3.8.


## From pip

```bash
pip install pyodk
```


## From source

```bash
# Get a copy of the repository.
mkdir -P ~/repos/pyodk
cd ~/repos/pyodk
git clone https://github.com/getodk/pyodk.git repo

# Create and activate a virtual environment for the install.
/usr/local/bin/python3.8 -m venv venv
source venv/bin/activate

# Install pyodk and its production dependencies.
cd ~/repos/pyodk/repo
pip install -e .

# Leave the virtualenv.
deactivate
```


# Configuration


## Main configuration file

The main configuration file uses the TOML format. The default file name is `.pyodk_config.toml`, and the default location is the user home directory. The file name and location can be customised by setting the environment variable `PYODK_CONFIG_FILE` to some other file path, or by passing the path at init with `Client(config_path="my_config.toml")`. The expected file structure is as follows:

```
[central]
base_url = "https://www.example.com"
username = "my_user"
password = "my_password"
default_project_id = 123
```


## Session cache file

The session cache file uses the TOML format. The default file name is `.pyodk_cache.toml`, and the default location is the user home directory. The file name and location can be customised by setting the environment variable `PYODK_CACHE_FILE` to some other file path, or by passing the path at init with `Client(config_path="my_cache.toml")`. This file should not be pre-created as it is used to store a session token after login.


# Usage

To get started with `pyODK`, build a `Client`:

```python
from pyodk.client import Client

client = Client()
```

Authentication is triggered by the first API call on the `Client`, or by explicitly using `Client.open()`.

Use `Client.close()` to clean up a client session. Clean up is recommended for long-running scripts, e.g. web apps, etc.

You can also use the Client as a context manager to manage authentication and clean up:

```python
with Client() as client:
    print(client.projects.list())
```

## Examples

**👉 See detailed Jupyter notebooks, scripts, and webinars [here](examples).**

```python
from pyodk.client import Client

client = Client()
projects = client.projects.list()
forms = client.forms.list()
submissions = client.submissions.list(form_id=next(forms).xmlFormId)
form_data = client.submissions.get_table(form_id="birds", project_id=8)
comments = client.submissions.list_comments(form_id=next(forms).xmlFormId, instance_id="uuid:...")
client.forms.update(
  form_id="my_xlsform",
  definition="my_xlsform.xlsx",
  attachments=["fruits.csv", "vegetables.png"],
)
client.close()
```

## Default project

The `Client` is not specific to a project, but a default `project_id` can be set by:

- A `default_project_id` in the configuration file.
- An init argument: `Client(project_id=1)`.
- A property on the client: `client.project_id = 1`.

## Custom configuration file paths

The `Client` is specific to a configuration and cache file. These approximately correspond to the session which the `Client` represents; it also encourages segregating credentials. These paths can be set by:

- Setting environment variables `PYODK_CONFIG_FILE` and `PYODK_CACHE_FILE`
- Init arguments: `Client(config_path="my_config.toml", cache_path="my_cache.toml")`.


## Methods

Available methods on `Client`:

- Projects
  - list: Read all Project details.
  - get: Read Project details.
  - create_app_users: Create new project app users, and optionally assign forms to them.
- Forms
  - list: Read all Form details.
  - get: Read Form details.
  - update: Create a new version of an existing Form.
- Submissions
  - list: Read all Submission metadata.
  - get: Read Submission metadata.
  - get_table: Read Submission data.
  - create: Create a Submission.
  - edit: Edit a submission, and optionally comment on it.
  - review: Update Submission metadata (review state), and optionally comment on it.
  - list_comments: Read Comment data for a Submission.
  - add_comment: Create a Comment for a Submission.

- *for additional requests*
  - get
  - post
  - put
  - patch
  - delete

See issues for additions to `pyodk` that are under consideration. Please file new issues for any functionality you are missing.

## Raw HTTP requests
For interacting with parts of the ODK Central API ([docs](https://odkcentral.docs.apiary.io)) that have not been implemented in `pyodk`, use HTTP verb methods exposed on the `Client`:

```
client.get("projects/8")
client.post("projects/7/app-users", json={"displayName": "Lab Tech"})
```
You can find a more detailed tutorial [in the examples](examples/).

These methods provide convenient access to `Client.session`, which is a `requests.Session` object subclass. The `Session` has customised to prefix request URLs with the `base_url` from the pyodk config. For example with a base_url `https://www.example.com`, a call to `client.session.get("projects/8")` gets the details of `project_id=8`, using the full url `https://www.example.com/v1/projects/8`.

## Session customization
If Session behaviour needs to be customised, for example to set alternative timeouts or retry strategies, etc., then subclass the `pyodk.session.Session` and provide an instance to the `Client` constructor, e.g. `Client(session=my_session)`.


## Logging

Errors and other messages are logged to a standard library `logging` logger in the `pyodk` namespace / hierarchy (e.g `pyodk.config`, `pyodk.endpoints.auth`, etc.). The logs can be manipulated from an application as follows.

```python
import logging


# Initialise an example basic logging config (writes to stdout/stderr).
logging.basicConfig()
logging.getLogger().setLevel(logging.DEBUG)

# Get a reference to the pyodk logger.
pyodk_log = logging.getLogger("pyodk")

# Receive everything DEBUG level and higher.
pyodk_log.setLevel(logging.DEBUG)
pyodk_log.propagate = True

# Ignore everything below FATAL level.
pyodk_log.setLevel(logging.FATAL)
pyodk_log.propagate = False
```


# Development

Install the source files as described above, then:

```sh
pip install -r dev_requirements.pip
```

You can run tests with:

```
nosetests
```

On Windows, use:

```
nosetests -v -v --traverse-namespace ./tests
```


# Releases

1. Run all linting and tests.
1. Draft a new GitHub release with the list of merged PRs.
1. Check out a release branch from latest upstream master.
1. Update `pyodk/__version__.py` with the new release version number.
1. Commit, push the branch, and initiate a pull request. Wait for tests to pass, then merge the PR.
1. Tag the release and it will automatically be published (see `release.yml` actions file).
