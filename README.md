# Pydantic-YAML

[![PyPI version](https://badge.fury.io/py/pydantic-yaml.svg)](https://badge.fury.io/py/pydantic-yaml) [![Documentation Status](https://readthedocs.org/projects/pydantic-yaml/badge/?version=latest)](https://pydantic-yaml.readthedocs.io/en/latest/?badge=latest)
 [![Unit Tests](https://github.com/NowanIlfideme/pydantic-yaml/actions/workflows/python-testing.yml/badge.svg)](https://github.com/NowanIlfideme/pydantic-yaml/actions/workflows/python-testing.yml)

Pydantic-YAML adds YAML capabilities to [Pydantic](https://pydantic-docs.helpmanual.io/),
which is an _excellent_ Python library for data validation and settings management.
If you aren't familiar with Pydantic, I would suggest you first check out their
[docs](https://pydantic-docs.helpmanual.io/).

[Documentation on ReadTheDocs.org](https://pydantic-yaml.readthedocs.io/en/latest/)

## Breaking Changes for v1

The API for `pydantic-yaml` version 1.0.0 has been greatly simplified!

You no longer need to add `YamlModel` or `YamlModelMixin` classes to your code,
unless you specifically want the `.yaml()` or `.parse_*()` methods.

## Basic Usage

```python
from enum import Enum
from pydantic import BaseModel, validator
from pydantic_yaml import parse_yaml_raw_as, to_yaml_str

class MyEnum(str, Enum):
    """A custom enumeration that is YAML-safe."""

    a = "a"
    b = "b"

class InnerModel(BaseModel):
    """A normal pydantic model that can be used as an inner class."""

    fld: float = 1.0

class MyModel(BaseModel):
    """Our custom class, with a `.yaml()` method.

    The `parse_raw()` and `parse_file()` methods are also updated to be able to
    handle `content_type='application/yaml'`, `protocol="yaml"` and file names
    ending with `.yml`/`.yaml`
    """

    x: int = 1
    e: MyEnum = MyEnum.a
    m: InnerModel = InnerModel()

    @validator("x")
    def _chk_x(cls, v: int) -> int:  # noqa
        """You can add your normal pydantic validators, like this one."""
        assert v > 0
        return v

m1 = MyModel(x=2, e="b", m=InnerModel(fld=1.5))

# This dumps to YAML and JSON respectively
yml = to_yaml_str(m1)
jsn = m1.json()

# This parses YAML as the MyModel type
m2 = parse_yaml_raw_as(MyModel, yml)
assert m1 == m2

# JSON is also valid YAML, so this works too
m3 = parse_yaml_raw_as(MyModel, jsn)
assert m1 == m3

```

## Mixin Class

This functionality has currently been removed!

## Configuration

You can configure the function used to dump and load the YAML by using the `Config`
inner class, [as in Pydantic](https://pydantic-docs.helpmanual.io/usage/model_config/):

```python
class MyModel(YamlModel):
    # ...
    class Config:
        # You can override these fields:
        yaml_dumps = my_custom_dumper
        yaml_loads = lambda x: MyModel()
        # As well as other Pydantic configuration:
        allow_mutation = False
```

## Versioned Models

This functionality has been removed, as it's questionably useful for most users.

If you were using the `VersionedModel` classes, you can use this snippet
in your own code:

```python
# TODO
```
