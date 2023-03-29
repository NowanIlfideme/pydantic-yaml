# Pydantic-YAML

[![PyPI version](https://badge.fury.io/py/pydantic-yaml.svg)](https://badge.fury.io/py/pydantic-yaml) [![Documentation Status](https://readthedocs.org/projects/pydantic-yaml/badge/?version=latest)](https://pydantic-yaml.readthedocs.io/en/latest/?badge=latest)
 [![Unit Tests](https://github.com/NowanIlfideme/pydantic-yaml/actions/workflows/python-testing.yml/badge.svg)](https://github.com/NowanIlfideme/pydantic-yaml/actions/workflows/python-testing.yml)

Pydantic-YAML adds YAML capabilities to [Pydantic](https://pydantic-docs.helpmanual.io/),
which is an _excellent_ Python library for data validation and settings management.
If you aren't familiar with Pydantic, I would suggest you first check out their
[docs](https://pydantic-docs.helpmanual.io/).

## Basic Usage

```python
from pydantic import BaseModel, validator
from pydantic_yaml import YamlStrEnum, YamlModel


class MyEnum(YamlStrEnum):
    """This is a custom enumeration that is YAML-safe."""

    a = "a"
    b = "b"

class InnerModel(BaseModel):
    """This is a normal pydantic model that can be used as an inner class."""

    fld: float = 1.0

class MyModel(YamlModel):
    """This is our custom class, with a `.yaml()` method.

    The `parse_raw()` and `parse_file()` methods are also updated to be able to
    handle `content_type='application/yaml'`, `protocol="yaml"` and file names
    ending with `.yml`/`.yaml`
    """

    x: int = 1
    e: MyEnum = MyEnum.a
    m: InnerModel = InnerModel()

    @validator('x')
    def _chk_x(cls, v: int) -> int:  # noqa
        """You can add your normal pydantic validators, like this one."""
        assert v > 0
        return v

m1 = MyModel(x=2, e="b", m=InnerModel(fld=1.5))

# This dumps to YAML and JSON respectively
yml = m1.yaml()
jsn = m1.json()

m2 = MyModel.parse_raw(yml)  # This automatically assumes YAML
assert m1 == m2

m3 = MyModel.parse_raw(jsn)  # This will fallback to JSON
assert m1 == m3

m4 = MyModel.parse_raw(yml, proto="yaml")
assert m1 == m4

m5 = MyModel.parse_raw(yml, content_type="application/yaml")
assert m1 == m5
```

## Mixin Class

Version 0.5.0 adds a `YamlModelMixin` which can be used to add YAML functionality on
top of, or alongside, other base classes:

```python
from typing import List

from pydantic import BaseModel
from pydantic_yaml import YamlModelMixin


class MyBase(BaseModel):
    """This is a normal."""
    x: str = "x"

class ExtModel(YamlModelMixin, MyBase):
    """This model can be sent to/read from YAML."""
    y: List[int] = [1, 2, 3]  # and you can define additional fields, if you want
```

Note that this `YamlModelMixin` must be **before** any `BaseModel`-derived classes.
This will hopefully be resolved in Pydantic 2.0
(see [this discussion](https://github.com/samuelcolvin/pydantic/discussions/3025)
for more details). If you know a better way of implementing this, please make raise
an issue or create a PR!

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

Since YAML is often used for config files, there is also a `SemVer` str-like class and `VersionedYamlModel` base class.

The `version` attribute is parsed according to the SemVer
([Semantic Versioning](https://semver.org/)) specification.
It's constrained between the `min_version` and `max_version` specified by your models'
`Config` inner class (similar to regular `pydantic` models).

### Usage example

```python
from pydantic import ValidationError
from pydantic_yaml import SemVer, VersionedYamlModel

class A(VersionedYamlModel):
    """Model with min, max constraints as None."""

    foo: str = "bar"


class B(VersionedYamlModel):
    """Model with a maximum version set."""

    foo: str = "bar"

    class Config:
        min_version = "2.0.0"

ex_yml = """
version: 1.0.0
foo: baz
"""

a = A.parse_raw(ex_yml)
assert a.version == SemVer("1.0.0")
assert a.foo == "baz"

try:
    B.parse_raw(ex_yml)
except ValidationError as e:
    print("Correctly got ValidationError:", e, sep="\n")
```
