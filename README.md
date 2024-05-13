# pyODK
[![pypi](https://img.shields.io/pypi/v/pyodk.svg)](https://pypi.python.org/pypi/pyodk)

An API client for the [ODK Central API](https://docs.getodk.org/central-api). Use it to interact with your data and automate common tasks from Python.

This library aims to make common data analysis and workflow automation tasks as simple as possible by providing clear method names, types, and examples. It also provides convenient access to the full API using [HTTP verb methods](https://getodk.github.io/pyodk/http-methods/).

## Install

The currently supported Python version for `pyodk` is 3.12. If this is different from the version you use for other projects, consider using [`pyenv`](https://github.com/pyenv/pyenv) to manage multiple versions of Python.

The currently supported Central version is v2024.1.0. Newer or older Central versions will likely work too, but convenience (non-HTTP) methods assume this version. If you see a 404 error or another server error, please verify the version of your Central server.

### From pip

```bash
pip install pyodk
```

### From source

```bash
# Get a copy of the repository.
mkdir -P ~/repos/pyodk
cd ~/repos/pyodk
git clone https://github.com/getodk/pyodk.git repo

# Create and activate a virtual environment for the install.
python -m venv venv
source venv/bin/activate

# Install pyodk and its production dependencies.
cd ~/repos/pyodk/repo
pip install -e .

# Leave the virtualenv.
deactivate
```

## Configure

The configuration file uses the TOML format. The default file name is `.pyodk_config.toml`, and the default location is the user home directory. The file name and location can be customised by setting the environment variable `PYODK_CONFIG_FILE` to some other file path, or by passing the path at init with `Client(config_path="my_config.toml")`. The expected file structure is as follows:

```toml
[central]
base_url = "https://www.example.com"
username = "my_user"
password = "my_password"
default_project_id = 123
```

### Custom configuration file paths

The `Client` is specific to a configuration and cache file. These approximately correspond to the session which the `Client` represents; it also encourages segregating credentials. These paths can be set by:

- Setting environment variables `PYODK_CONFIG_FILE` and `PYODK_CACHE_FILE`
- Init arguments: `Client(config_path="my_config.toml", cache_path="my_cache.toml")`.

### Default project

The `Client` is not specific to a project, but a default `project_id` can be set by:

- A `default_project_id` in the configuration file.
- An init argument: `Client(project_id=1)`.
- A property on the client: `client.project_id = 1`.

*Default Identifiers*

For each endpoint, a default can be set for key identifiers, so these identifiers are optional in most methods. When the identifier is required, validation ensures that either a default value is set, or a value is specified. E.g.

```python
client.projects.default_project_id = 1
client.forms.default_form_id = "my_form"
client.submissions.default_form_id = "my_form"
client.entities.default_entity_list_name = "my_list"
client.entities.default_project_id = 1
```

### Session cache file

The session cache file uses the TOML format. The default file name is `.pyodk_cache.toml`, and the default location is the user home directory. The file name and location can be customised by setting the environment variable `PYODK_CACHE_FILE` to some other file path, or by passing the path at init with `Client(config_path="my_cache.toml")`. This file should not be pre-created as it is used to store a session token after login.

## Use

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

Learn more [in the documentation](https://getodk.github.io/pyodk/).

### Examples

**👉 See detailed tutorials in [the documentation](https://getodk.github.io/pyodk/examples/).**

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

### Session customization
If Session behaviour needs to be customised, for example to set alternative timeouts or retry strategies, etc., then subclass the `pyodk.session.Session` and provide an instance to the `Client` constructor, e.g. `Client(session=my_session)`.


### Logging
Errors raised by pyODK and other messages are logged using the `logging` standard library. The logger is in the `pyodk` namespace / hierarchy (e.g `pyodk.config`, `pyodk.endpoints.auth`, etc.). The logs can be manipulated from your script / app as follows.

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

### Errors raised by pyODK
Error types raised by pyODK are found in `errors.py`, which currently is only the `PyODKError`. In general this error is raised when:

- The pyODK configuration is invalid (missing file, missing fields, etc).
- The client method arguments are invalid (missing, wrong type, etc.).
- The response from ODK Central indicated and error (HTTP >=400, <600).
- The data returned from ODK Central does not have the expected fields or types.

Note that pyODK does not attempt to wrap every possible error condition, so if needed, broader exception handling should be included in your script / app.

## Design considerations
Our goal with pyODK is to support the most common Central API functionality in an easy-to-use, high-level way. Because we expose [HTTP verb methods](https://getodk.github.io/pyodk/http-methods/), we don't feel the need to add explicit support for the whole Central API.

Here are some points to think about when considering adding new methods to pyODK:

* Is it common enough to warrant a designed method or can we show examples using the HTTP methods if needed?
  * For example, we currently consider manipulating form drafts directly out of scope but `client.forms.update` implicitly creates and publishes a draft
* Do people take this action independently or is it always part of reaching some broader goal?
* What pyODK class does it best fit in?
  * For example, form versions are subresources on Central backend but in this library, methods that deal with form versions can be in the `forms` class directly since we’re not going to expose many of them
* How do people talk about the action that’s being performed? How do ODK docs and Central frontend talk about it?
  * For example, documentation has the concept of "submission edits" so use `client.submissions.edit` rather than update
* Value expressiveness and consistency with ODK concepts over pyODK internal consistency
  * What actually needs to be commonly configured? Starting by exposing a subset of parameters and naming/typing them carefully is ideal.

## Contribute

See issues for additions to `pyodk` that are under consideration. Please file new issues for any functionality you are missing.

## Develop

Install the source files as described above, then:

```bash
pip install -e .[dev]
```

You can run tests with:

```bash
python -m unittest
```

### Testing

When adding or updating pyODK functionality, at a minimum add or update corresponding unit tests. The unit tests are filed in `tests/endpoints` or `tests`. These tests focus on pyODK functionality, such as ensuring that data de/serialisation works as expected, and that method logic results in the expected call patterns. The unit tests use mocks and static data, which are stored in `tests/resources`. These data are obtained by making an API call and saving the Python dict returned by `response.json()` as text.

For interactive testing, debugging, or sanity checking workflows, end-to-end tests are stored in `tests/test_client.py`. These tests are not run by default because they require access to a live Central server. The ODK team use the Central staging instance https://staging.getodk.cloud/ which is already configured for testing. Below are the steps to set up a new project in Central to be able to run these tests.

1. Create a test project in Central.
2. Create a test user in Central. It can be a site-wide Administrator. If it is not an Administrator, assign the user to the project with "Project Manager" privileges, so that forms and submissions in the test project can be uploaded and modified.
3. Save the user's credentials and the project ID in a `.pyodk_config.toml` (or equivalent) as described in the above section titled "Configure".
4. When the tests in `test_client.py` are run, the test setup method should automatically create a few fixtures for testing with. At a minimum these allow the tests to pass, but can also be used to interactively test or debug.


## Release

1. Run all linting and tests.
1. Draft a new GitHub release with the list of merged PRs.
1. Check out a release branch from latest upstream master.
1. Update `pyproject.toml` and `pyodk/__version__.py` with the new release version number.
1. Update the Central version in the README to reflect the version we test against.
1. Commit, push the branch, and initiate a pull request. Wait for tests to pass, then merge the PR.
1. Tag the release and it will automatically be published (see `release.yml` actions file).
