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

# You can also auto-generate comments in YAML from the model docstrings and field descriptions -
# see "Configuration" below for how `add_comments` and other options work via the engine object
from pydantic_yaml import RuamelEngine
print(to_yaml_str(m1, engine=RuamelEngine(add_comments=True)))
```

See [comment generation docs](docs/comments.md) for more info.

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

All YAML-specific configuration - formatting, comments, JSON-dump kwargs - lives on the
**engine** object you pass as `engine=`, not on `to_yaml_str`/`to_yaml_file` themselves. See
[YAML Engine](#yaml-engine) below for the full picture; in short:

```python
from pydantic_yaml import RuamelEngine, to_yaml_str

to_yaml_str(model, engine=RuamelEngine(indent=4))                        # wider indent
to_yaml_str(model, engine=RuamelEngine(map_indent=9, sequence_indent=7)) # ... you monster.
to_yaml_str(model, engine=RuamelEngine(add_comments=True))               # docstrings as comments
to_yaml_str(model, engine=RuamelEngine(sort_keys=True))                  # alphabetize keys
```

Engines are immutable (frozen `pydantic.BaseModel`s); derive a variant with
`.model_copy(update=...)` instead of mutating one:

```python
base_engine = RuamelEngine(indent=4)
with_comments = base_engine.model_copy(update={"add_comments": True})
```

You can also pass your own pre-built `ruamel.yaml.YAML` instance:

```python
from ruamel.yaml import YAML
from pydantic_yaml import RuamelEngine, to_yaml_file

my_writer = YAML(typ="safe")
my_writer.default_flow_style = True
to_yaml_file("foo.yaml", model, engine=RuamelEngine(default_flow_style=None, writer=my_writer))
```

## YAML Engine

`pydantic-yaml` reads/writes YAML through a pluggable **engine** object - any object with
`read(stream)`/`write(stream, model)` methods works, so you can bring your own YAML library, or
serialize by hand (bypassing JSON entirely) for full control. See
[issue #338](https://github.com/NowanIlfideme/pydantic-yaml/issues/338) and the "YAML
Customization" milestone for the motivation.

Two built-in engines ship out of the box:

- [`YamlRocksEngine`](https://yaml.rocks) - backed by `yamlrocks`, a Rust engine that's YAML 1.2
  spec-compliant and, unlike `ruamel.yaml`, passes the
  [yaml-test-suite](https://github.com/yaml/yaml-test-suite). **Recommended.**
- [`RuamelEngine`](https://yaml.readthedocs.io/) - backed by `ruamel.yaml`, the historical default.

Neither backend is a core dependency - **at least one must be installed, but either one suffices**:

```sh
pip install "pydantic-yaml[yamlrocks]"  # recommended; requires Python >=3.12
pip install "pydantic-yaml[ruamel]"     # matches the historical default
pip install "pydantic-yaml[all]"        # both
```

If you don't pick an engine explicitly, whichever is installed is used automatically (preferring
`YamlRocksEngine` if both are). Installing neither raises a clear `ImportError` the first time
you actually read or write YAML (importing `pydantic_yaml` itself still works).

Pass a configured engine object per-call:

```python
from pydantic_yaml import YamlRocksEngine, to_yaml_str, parse_yaml_raw_as

to_yaml_str(model, engine=YamlRocksEngine(sort_keys=True))
parse_yaml_raw_as(MyModel, yml, engine=YamlRocksEngine())
```

or switch the default for the whole process:

```python
from pydantic_yaml import RuamelEngine, set_default_engine

set_default_engine(RuamelEngine(indent=4))
```

There's no string-based engine selection (no `engine="yamlrocks"`, no `PYDANTIC_YAML_ENGINE` env
var) - always an actual engine object, so `engine=`/`set_default_engine()` work identically for
the built-ins and for anything you write yourself.

Some `RuamelEngine`-only fields (`writer`, independently-configurable
`map_indent`/`sequence_indent`/`sequence_dash_offset`) simply don't exist on `YamlRocksEngine`,
since that library has no equivalent knobs - passing them raises a `ValidationError`
immediately, rather than a runtime error deep inside a dump call. Field order is preserved by
default on both engines (pass `sort_keys=True` to alphabetize instead), and multiline strings
dump in block-literal (`|`) style unconditionally on both - there's no toggle for this, since
`yamlrocks` has no way to disable it either.

### Writing a custom engine

Any object with the right two methods works - no inheritance required:

```python
from io import IOBase
from typing import Any
from pydantic import BaseModel
from pydantic_yaml import to_yaml_str

class MyEngine:
    def read(self, stream: IOBase) -> Any:
        ...  # parse `stream` into plain Python objects

    def write(self, stream: IOBase, model: BaseModel) -> None:
        ...  # serialize `model` to `stream`, however you like - JSON is not required

to_yaml_str(model, engine=MyEngine())
```

`isinstance(your_engine, YamlEngine)` works too (`YamlEngine` is a `@runtime_checkable`
`Protocol`), if you want to check conformance explicitly.

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
There is an [example in the docs](docs/versioned.md) that's available.
