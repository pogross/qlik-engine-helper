[![Python 3.8](https://img.shields.io/badge/python-3.8-blue)](https://www.python.org) [![Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black) [![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)

# Qlik Engine Helper

**A cli tool to simplify the use of the [Qlik Engine JSON API](https://help.qlik.com/en-US/sense-developer/November2020/Subsystems/EngineAPI/Content/Sense_EngineAPI/introducing-engine-API.htm)**

## Features

:warning: **Currently this works with Qlik Sense Desktop only** :warning:
Future version will implement authentication strategies for Qlik Sense Servers

- Create new apps
- List available apps
- Extract, replace and append script code

## Installation

The package is currently not PyPi, therefore you have to install directly from the Github Repo

```bash
pip install git+https://github.com/pogross/qlik-engine-helper
```

## Usage

In your terminal use `qlik-engine-helper <commands>`

`qlik-engine-helper --help` provides help messages
`--help` is also avaiable for sub-commands, e.g., `qlik-engine-helper app --help`

### Commands

Creates a new empty app

```bash
qlik-engine-helper app create --name [AppName]
```

List of available apps (name, id, last reload)

```bash
qlik-engine-helper app list
```

Extract script code from app and save it to local .qvs files

```bash
qlik-engine-helper app get-script --app-id [appID]
```

Overwrite existing script code with code from local .qvs files

```bash
qlik-engine-helper app append-script --app-id [appID] --code [PATH]
```

Appends script code from .qvs files to the existing script code

```bash
qlik-engine-helper app append-script
```

## Devs / Contributors

We recommend to use a UNIX-based enviroment. For Ubuntu users take a look at python [deadsnakes](https://launchpad.net/~deadsnakes/+archive/ubuntu/ppa).

We use [poetry](https://github.com/python-poetry/poetry) and `pyproject.toml` for managing packages, dependencies and some settings.

### Setup virtual environment for development

You should follow the [instructions](https://github.com/python-poetry/poetry) to get poetry up and running for your system. We recommend to use a UNIX-based development system (Linux, Mac, WSL). After setting up poetry you can use `poetry install` within the project folder to install all dependencies.

The poetry virtual environment should be available in the the project folder as `.venv` folder as specified in `poetry.toml`. This helps with `.venv` detection in IDEs.

#### Conda users

If you use the Anaconda Python distribution (strongly recommended for Windows users) and `conda create` for your virtual environments, then you will not be able to use the `.venv` environment created by poetry because it is not a conda environment. If you want to use `poetry` disable poetry's behavior of creating a new virtual environment with the following command: `poetry config virtualenvs.create false`. You can add `--local` if you don't want to change this setting globally but only for the current project. See the [poetry configuration docs](https://python-poetry.org/docs/configuration/) for more details.

Now, when you run `poetry install`, poetry will install all dependencies to your conda environment. You can verify this by running `pip freeze` after `poetry install`.

### [pre-commit](https://pre-commit.com/)

To ensure consistency you should use pre-commit. `pip install pre-commit` and after cloning the karmabot repo run `pre-commit install` within the project folder.

This will enable pre-commit hooks for checking before every commit.

Otherwise, you can always run `pre-commit run --all-files` at any time.
