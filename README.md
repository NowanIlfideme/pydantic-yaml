# pydantic-yaml

[![PyPI version](https://badge.fury.io/py/pydantic-yaml.svg)](https://badge.fury.io/py/pydantic-yaml) [![Unit Tests](https://github.com/NowanIlfideme/pydantic-yaml/actions/workflows/python-testing.yml/badge.svg)](https://github.com/NowanIlfideme/pydantic-yaml/actions/workflows/python-testing.yml)

This is a small helper library that adds some YAML capabilities to [pydantic](https://github.com/samuelcolvin/pydantic), namely dumping to yaml via the `yaml_model.yaml()` function, and parsing from strings/files using `YamlModel.parse_raw()` and `YamlModel.parse_file()`. It also adds `Enum` subclasses that get dumped to YAML as strings or integers, and fixes dumping of some typical types.

## Basic Usage

Example usage is seen below.

```python
from pydantic_yaml import YamlStrEnum, YamlModel


class MyEnum(YamlStrEnum):
    a = "a"
    b = "b"


class MyModel(YamlModel):
    x: int = 1
    e: MyEnum = MyEnum.a

m1 = MyModel(x=2, e="b")
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

## Installation

`pip install pydantic_yaml`

Make sure to install `ruamel.yaml` or `pyyaml` as well. These are optional dependencies:

`pip install pydantic_yaml[ruamel]`

`pip install pydantic_yaml[pyyaml]`

## Versioned Models

NOTE: This is currently not implemented!

Since YAML is often used for config files, there is also a `VersionedYamlModel` class.

The `version` attribute is parsed according to the SemVer
([Semantic Versioning](https://semver.org/)) specification.

Usage example:

```python
from pydantic import ValidationError
from pydantic_yaml import VersionedYamlModel

class A(VersionedYamlModel):
    foo: str = "bar"


class B(VersionedYamlModel):
    foo: str = "bar"

    class Config:
        min_version = "2.0.0"

yml = """
version: 1.0.0
foo: baz
"""

A.parse_raw(yml)

try:
    B.parse_raw(yml)
except ValidationError as e:
    print("Correctly got ValidationError:", e, sep="\n")
```
