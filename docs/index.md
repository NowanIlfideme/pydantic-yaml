# Pydantic-YAML

[![PyPI version](https://badge.fury.io/py/pydantic-yaml.svg)](https://badge.fury.io/py/pydantic-yaml) [![Documentation Status](https://readthedocs.org/projects/pydantic-yaml/badge/?version=latest)](https://pydantic-yaml.readthedocs.io/en/latest/?badge=latest)
 [![Unit Tests](https://github.com/NowanIlfideme/pydantic-yaml/actions/workflows/python-testing.yml/badge.svg)](https://github.com/NowanIlfideme/pydantic-yaml/actions/workflows/python-testing.yml)

Pydantic-YAML adds YAML capabilities to [Pydantic](https://pydantic-docs.helpmanual.io/),
which is an _excellent_ Python library for data validation and settings management.
If you aren't familiar with Pydantic, I would suggest you first check out their
[docs](https://pydantic-docs.helpmanual.io/).

[Documentation on ReadTheDocs.org](https://pydantic-yaml.readthedocs.io/en/latest/)

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
    """Our custom Pydantic model."""

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

# You can also auto-generate comments in YAML from the model docstrings and field descriptions
print(to_yaml_str(m1, add_comments=True))
```

See [comment generation docs](comments.md) for more info.

With Pydantic v2, you can also dump dataclasses:

```python
from pydantic import RootModel
from pydantic.dataclasses import dataclass
from pydantic.version import VERSION as PYDANTIC_VERSION
from pydantic_yaml import to_yaml_str

assert PYDANTIC_VERSION >= "2"

@dataclass
class YourType:
    foo: str = "bar"

obj = YourType(foo="wuz")
assert to_yaml_str(RootModel[YourType](obj)) == 'foo: wuz\n'
```

## Configuration

Currently we use the JSON dumping of Pydantic to perform most of the magic.

This uses the `Config` inner class,
[as in Pydantic](https://pydantic-docs.helpmanual.io/usage/model_config/):

```python
class MyModel(BaseModel):
    # ...
    class Config:
        # You can override these fields, which affect JSON and YAML:
        json_dumps = my_custom_dumper
        json_loads = lambda x: MyModel()
        # As well as other Pydantic configuration:
        allow_mutation = False
```

You can control some YAML-specfic options via the keyword options:

```python
to_yaml_str(model, indent=4)  # Makes it wider
to_yaml_str(model, map_indent=9, sequence_indent=7)  # ... you monster.
```

You can additionally pass your own `YAML` instance:

```python
from ruamel.yaml import YAML
my_writer = YAML(typ="safe")
my_writer.default_flow_style = True
to_yaml_file("foo.yaml", model, custom_yaml_writer=my_writer)
```

A separate configuration for YAML specifically will be added later, likely in v2.

## YAML Engine

`pydantic-yaml` supports two YAML backends, as tracked in
[issue #338](https://github.com/NowanIlfideme/pydantic-yaml/issues/338):

- [`yamlrocks`](https://yaml.rocks) - a Rust-backed engine that's YAML 1.2 spec-compliant and,
  unlike `ruamel.yaml`, passes the [yaml-test-suite](https://github.com/yaml/yaml-test-suite).
  **Recommended.**
- [`ruamel.yaml`](https://yaml.readthedocs.io/) - the historical default.

Neither is a core dependency - **at least one must be installed, but either one suffices**:

```sh
pip install "pydantic-yaml[yamlrocks]"  # recommended; requires Python >=3.12
pip install "pydantic-yaml[ruamel]"     # matches the historical default
pip install "pydantic-yaml[all]"        # both
```

If you don't pick one explicitly, whichever is installed is used automatically (preferring
`yamlrocks` if both are present). Installing neither raises a clear `ImportError` the first
time you actually read or write YAML (importing `pydantic_yaml` itself still works).

Select an engine per-call:

```python
to_yaml_str(model, engine="yamlrocks")
parse_yaml_raw_as(MyModel, yml, engine="yamlrocks")
```

or switch the default for the whole process:

```python
from pydantic_yaml import set_default_engine

set_default_engine("yamlrocks")  # or set PYDANTIC_YAML_ENGINE=yamlrocks
```

Some `ruamel`-specific options (`custom_yaml_writer`, independently-configurable
`map_indent`/`sequence_indent`/`sequence_dash_offset`) aren't supported by the `yamlrocks`
engine, since that library doesn't expose equivalent knobs.

## Breaking Changes for `pydantic-yaml` V1

The API for `pydantic-yaml` version 1.0.0 has been greatly simplified!

### Mixin Class

This functionality has currently been removed!
`YamlModel` and `YamlModelMixin` base classes are no longer needed.
The plan is to re-add it before v1 fully releases,
to allow the `.yaml()` or `.parse_*()` methods.
However, this will be availble only for `pydantic<2`.

### Versioned Models

This functionality has been removed, as it's questionably useful for most users.
There is an [example in the docs](versioned.md) that's available.
