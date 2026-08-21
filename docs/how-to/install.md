# Install pydantic-yaml

## Pick a YAML backend

`pydantic-yaml` needs a YAML backend to actually read/write YAML, but doesn't require a specific
one - install at least one of the following extras (see
[Why a pluggable YAML engine?](../explanation/engine-design.md) for the reasoning):

```sh
pip install "pydantic_yaml[yamlrocks]"  # yamlrocks, a Rust-backed engine; requires Python >=3.12
pip install "pydantic_yaml[ruamel]"     # ruamel.yaml, the historical default
pip install "pydantic_yaml[all]"        # both
```

If you install both, `yamlrocks` is used by default; see
[Choose and configure a YAML engine](configure-engine.md) for how to pick or switch.

## Set up a development environment

To contribute to `pydantic-yaml` itself, clone the repo and sync with
[`uv`](https://docs.astral.sh/uv/) (what the project itself uses for dependency management,
testing, and CI):

```sh
git clone https://github.com/NowanIlfideme/pydantic-yaml.git
cd pydantic-yaml
uv sync
```

This installs the `dev` and `docs` dependency groups (linting, type checking, tests,
documentation tooling) alongside both YAML backends.
