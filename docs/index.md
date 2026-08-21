# Pydantic-YAML

Pydantic-YAML adds YAML reading and writing to [Pydantic](https://docs.pydantic.dev/) models:
dump any `BaseModel` to a YAML string or file, and parse YAML back into a validated model.

```python
from pydantic import BaseModel
from pydantic_yaml import parse_yaml_raw_as, to_yaml_str

class Config(BaseModel):
    name: str
    retries: int = 3

cfg = Config(name="prod")
print(to_yaml_str(cfg))
# name: prod
# retries: 3

assert parse_yaml_raw_as(Config, "name: prod\nretries: 3\n") == cfg
```

It also supports generating YAML comments from your model's docstrings and field descriptions,
and a pluggable YAML engine - bring your own YAML library, or hand-write serialization, if the
two built-in engines don't do what you need.

## Where to go next

This documentation follows the [Diátaxis](https://diataxis.fr/) framework, organized into four
sections:

- **[Tutorial](tutorial/getting-started.md)** - a step-by-step introduction if you're new to
  `pydantic-yaml`. Start here.
- **How-to guides** - task-focused recipes for specific things you want to do:
    - [Install pydantic-yaml](how-to/install.md)
    - [Add comments to YAML output](how-to/add-comments.md)
    - [Choose and configure a YAML engine](how-to/configure-engine.md)
    - [Write a custom YAML engine](how-to/write-custom-engine.md)
    - [Dump Pydantic dataclasses](how-to/dump-dataclasses.md)
    - [Recover versioned models](how-to/recover-versioned-models.md) (a feature removed in v1)
- **[Reference](reference/api.md)** - complete API documentation, generated from the source.
- **Explanation** - background and design rationale:
    - [Why a pluggable YAML engine?](explanation/engine-design.md)
    - [Breaking changes across versions](explanation/changelog.md)
