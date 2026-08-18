# Installation

## Manually

The easiest way to get started is through pip:

```sh
pip install pydantic_yaml
```

This will install the latest supported `pydantic` and `ruamel.yaml` as well,
unless you already have a compatible version.

To use the optional, Rust-backed [`yamlrocks`](https://yaml.rocks) engine instead
(see [issue #338](https://github.com/NowanIlfideme/pydantic-yaml/issues/338)), install the extra
(requires Python >=3.12):

```sh
pip install "pydantic_yaml[yamlrocks]"
```

## Development Installation

For development, you can install in editable mode with dependencies:

```sh
git clone https://github.com/NowanIlfideme/pydantic-yaml.git
cd pydantic-yaml
pip install -e ".[dev,docs]"
```

Or, better yet, you can use the provided `conda` environment for development.
