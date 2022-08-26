# pyODK

An API client for ODK Central that makes it easier to interact with data in ODK from Python.

More details on the goals and implementation plans [are here](https://docs.google.com/document/d/1AamUcvO4R7VzphToIfeMhCjWEjxjbpVQ_DJR89FlpRc/edit).


# Install

The currently supported Python version for `pyodk` is 3.8.


## From pip

```
pip install pyodk
```


## From source

```
# Get a copy of the repository.
mkdir -P ~/repos/pyodk
cd ~/repos/pyodk
git clone https://github.com/getodk/pyodk.git repo

# Create and activate a virtual environment for the install.
/usr/local/bin/python3.8 -m venv venv
source venv/bin/activate

# Install pyodk and it's production dependencies.
cd ~/repos/pyodk/repo
pip install -e .

# Leave the virtualenv.
deactivate
```


# Configuration


## Main configuration file

The main configuration file uses the TOML format. The default file name is `.pyodk_config.toml`, and the default location is the user home directory. The file name and location can be customised by setting the environment variable `PYODK_CONFIG_FILE` to some other file path. The expected file structure is as follows:

```
[central]
base_url = "https://www.example.com"
username = "my_user"
password = "my_password"
default_project_id = "123"
```


## Session cache file

The session cache file uses the TOML format. THe default file name is `.pyodk_cache.toml`, and the default location is the user home directory. The file name and location can be customised by setting the environment variable `PYODK_CACHE_FILE` to some other file path. This file should not be pre-configured as it is used to store a session token after login.


# Development

Install the source files as described above, then:

```
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
2. Draft a new GitHub release with the list of merged PRs.
3. Checkout a release branch from latest upstream master.
4. Update `CHANGES.md` with the text of the draft release.
5. Update `pyodk/__init__.py` with the new release version number.
6. Commit, push the branch, and initiate a pull request. Wait for tests to pass, then merge the PR.
7. Tag the release and it will automatically be published (see `release.yml` actions file).
