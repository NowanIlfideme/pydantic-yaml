# Installation

## Manually

The easiest way to get started is through pip:

```sh
pip install pydantic_yaml
```

Make sure you have `ruamel.yaml` or `pyyaml` installed as well.
You can define ensure these via extra dependencies:

`pip install pydantic_yaml[ruamel]`

`pip install pydantic_yaml[pyyaml]`

## Development Installation

For development, you can install in editable mode with dependencies:

```sh
git clone https://github.com/NowanIlfideme/pydantic-yaml.git
cd pydantic-yaml
pip install -e ".[dev,docs,ruamel]"
```

Or you can use the provided `conda` environment for development.
