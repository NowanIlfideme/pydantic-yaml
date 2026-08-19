# Installation

## Manually

`pydantic-yaml` needs a YAML backend to actually read/write YAML, but doesn't require a specific
one - install at least one of the following extras (see
[issue #338](https://github.com/NowanIlfideme/pydantic-yaml/issues/338)):

```sh
pip install "pydantic_yaml[yamlrocks]"  # yamlrocks, a Rust-backed engine; requires Python >=3.12
pip install "pydantic_yaml[ruamel]"     # ruamel.yaml, the historical default
pip install "pydantic_yaml[all]"        # both
```

If you install both, `yamlrocks` is used by default; see
[Configuration](index.md#yaml-engine) for how to pick or switch engines.

## Development Installation

For development, you can install in editable mode with dependencies:

```sh
git clone https://github.com/NowanIlfideme/pydantic-yaml.git
cd pydantic-yaml
pip install -e ".[dev,docs]"
```

Or, better yet, you can use the provided `conda` environment for development.
