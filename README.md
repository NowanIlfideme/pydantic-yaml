# Pydantic-YAML

[![PyPI version](https://badge.fury.io/py/pydantic-yaml.svg)](https://badge.fury.io/py/pydantic-yaml) [![Documentation Status](https://readthedocs.org/projects/pydantic-yaml/badge/?version=latest)](https://pydantic-yaml.readthedocs.io/en/latest/?badge=latest)
 [![Unit Tests](https://github.com/NowanIlfideme/pydantic-yaml/actions/workflows/python-testing.yml/badge.svg)](https://github.com/NowanIlfideme/pydantic-yaml/actions/workflows/python-testing.yml)

Pydantic-YAML adds YAML reading and writing to [Pydantic](https://docs.pydantic.dev/) models:
dump any `BaseModel` to a YAML string or file, and parse YAML back into a validated model.

[Full documentation on ReadTheDocs.org](https://pydantic-yaml.readthedocs.io/en/latest/)

## Installation

```sh
pip install "pydantic_yaml[yamlrocks]"  # recommended; requires Python >=3.12
```

`pydantic-yaml` needs at least one YAML backend - `[ruamel]` and `[all]` are also available. See
[Install pydantic-yaml](docs/how-to/install.md) for the full picture.

## Quick example

```python
from pydantic import BaseModel
from pydantic_yaml import parse_yaml_raw_as, to_yaml_str

class Config(BaseModel):
    name: str
    retries: int = 3

cfg = Config(name="prod")
yml = to_yaml_str(cfg)
print(yml)
# name: prod
# retries: 3

assert parse_yaml_raw_as(Config, yml) == cfg
```

`pydantic-yaml` also supports:

- generating YAML comments from your model's docstrings and field descriptions - see
  [Add comments to YAML output](docs/how-to/add-comments.md),
- a pluggable YAML engine - bring your own YAML library, or hand-write serialization - see
  [Choose and configure a YAML engine](docs/how-to/configure-engine.md) and
  [Write a custom YAML engine](docs/how-to/write-custom-engine.md), and
- dumping Pydantic dataclasses - see [Dump Pydantic dataclasses](docs/how-to/dump-dataclasses.md).

See the [full documentation](https://pydantic-yaml.readthedocs.io/en/latest/) for a guided
[tutorial](docs/tutorial/getting-started.md), task-focused how-to guides, a complete
[API reference](docs/reference/api.md), and [design explanations](docs/explanation/engine-design.md) -
organized following the [Diátaxis](https://diataxis.fr/) framework.
