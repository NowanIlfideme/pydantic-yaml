# Getting Started

This tutorial walks through the basics of `pydantic-yaml`: installing it, defining a model,
dumping it to YAML, and reading YAML back. By the end you'll have a working example you can
build on.

## 1. Install

`pydantic-yaml` needs a YAML backend to actually read and write YAML. Install it with the
`yamlrocks` extra (recommended):

```sh
pip install "pydantic_yaml[yamlrocks]"
```

`yamlrocks` requires Python 3.12+. If you're on an older Python, use
`pip install "pydantic_yaml[ruamel]"` instead - see [Install pydantic-yaml](../how-to/install.md)
for every option.

## 2. Define a model

`pydantic-yaml` works with any [Pydantic](https://docs.pydantic.dev/) model - nothing special to
inherit from:

```python
from pydantic import BaseModel

class Address(BaseModel):
    street: str
    city: str

class User(BaseModel):
    name: str
    age: int
    address: Address
```

## 3. Dump a model to YAML

```python
from pydantic_yaml import to_yaml_str

user = User(name="Ada", age=30, address=Address(street="1 Infinite Loop", city="Cupertino"))
print(to_yaml_str(user))
```

```yaml
name: Ada
age: 30
address:
  street: 1 Infinite Loop
  city: Cupertino
```

## 4. Parse YAML back into a model

```python
from pydantic_yaml import parse_yaml_raw_as

yaml_text = """
name: Ada
age: 30
address:
  street: 1 Infinite Loop
  city: Cupertino
"""

loaded = parse_yaml_raw_as(User, yaml_text)
assert loaded == user
```

Pydantic validates the data exactly as it would for `User(**data)` - a wrong type or a missing
required field raises `pydantic.ValidationError`, same as always.

## 5. Read and write files directly

```python
from pydantic_yaml import to_yaml_file, parse_yaml_file_as

to_yaml_file("user.yaml", user)
loaded = parse_yaml_file_as(User, "user.yaml")
assert loaded == user
```

## Next steps

You've covered the core workflow. From here:

- [Add comments to YAML output](../how-to/add-comments.md), generated from your model's
  docstrings and field descriptions.
- [Choose and configure a YAML engine](../how-to/configure-engine.md) to control formatting, or
  pick between the two built-in backends.
- Browse the [API reference](../reference/api.md) for the full picture.
