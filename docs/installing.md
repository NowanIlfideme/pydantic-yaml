# Installation

## Manually

The easiest way to get started is through pip:

```sh
pip install pydantic_yaml
```

This will install the latest supported `pydantic` and `ruamel.yaml` as well,
unless you already have a compatible version.

## Development Installation

For development, you can install in editable mode with dependencies:

```sh
git clone https://github.com/NowanIlfideme/pydantic-yaml.git
cd pydantic-yaml
pip install -e ".[dev,docs]"
```

Or, better yet, you can use the provided `conda` environment for development.
