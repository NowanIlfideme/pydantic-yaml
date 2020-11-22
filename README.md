# pydantic-yaml

This is a small helper library that adds some YAML capabilities to [pydantic](https://github.com/samuelcolvin/pydantic), namely dumping to yaml via the `yaml_model.yaml()` function, and parsing from strings/files using `YamlModel.parse_raw()` and `YamlModel.parse_file()`. It also adds an `Enum` subclass that gets dumped to YAML as a string, and fixes dumping of some typical types.

## Usage

Example usage is seen below.

```python
from pydantic_yaml import YamlEnum, YamlModel


class MyEnum(str, YamlEnum):
    a = "a"
    b = "b"


class MyModel(YamlModel):
    x: int = 1
    e: MyEnum = MyEnum.a

m1 = MyModel(x=2, e="b")
yml = m1.yaml()

m2 = MyModel.parse_raw(yml, proto="yaml")
assert m1 == m2

m3 = MyModel.parse_raw(yml, content_type="application/yaml")
assert m1 == m3
```

## Installation

`pip install pydantic_yaml`

Make sure to install `ruamel.yaml` (recommended) or `pyyaml` as well. These are optional dependencies:

`pip install pydantic_yaml[ruamel]`

`pip install pydantic_yaml[pyyaml]`
