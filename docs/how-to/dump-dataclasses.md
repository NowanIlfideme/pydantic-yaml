# Dump Pydantic Dataclasses

`pydantic-yaml`'s functions all expect a `pydantic.BaseModel`, so a
[Pydantic dataclass](https://docs.pydantic.dev/latest/concepts/dataclasses/) needs wrapping in a
`RootModel` first:

```python
from pydantic import RootModel
from pydantic.dataclasses import dataclass
from pydantic_yaml import to_yaml_str, parse_yaml_raw_as

@dataclass
class YourType:
    foo: str = "bar"

obj = YourType(foo="wuz")
assert to_yaml_str(RootModel[YourType](obj)) == "foo: wuz\n"
```

Parsing back works the same way - the loaded value is on `.root`:

```python
loaded = parse_yaml_raw_as(RootModel[YourType], "foo: wuz\n")
assert loaded.root == obj
```

Everything else - [comments](add-comments.md), [engine configuration](configure-readers-writers.md) -
works exactly as it does for a regular `BaseModel`, since `RootModel[YourType]` *is* one.
