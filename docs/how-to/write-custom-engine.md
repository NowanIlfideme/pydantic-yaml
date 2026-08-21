# Write a Custom YAML Engine

`pydantic-yaml`'s two built-in engines are just implementations of the `YamlEngine` protocol -
any object with `read(stream)`/`write(stream, model)` methods works, no inheritance required.
Bring your own YAML library, or serialize by hand (bypassing JSON entirely) for full control. See
[Why a pluggable YAML engine?](../explanation/engine-design.md) for the motivation.

## The protocol

```python
from io import IOBase
from typing import Any, Protocol, runtime_checkable
from pydantic import BaseModel

@runtime_checkable
class YamlEngine(Protocol):
    def read(self, stream: IOBase) -> Any:
        """Read a YAML stream into plain Python objects, for TypeAdapter validation."""
        ...

    def write(self, stream: IOBase, model: BaseModel) -> None:
        """Write `model` as YAML to `stream`, using this engine's own configuration."""
        ...
```

(This is the actual definition, importable as `pydantic_yaml.YamlEngine` - shown here for
reference.)

## A minimal custom engine

Any object with the right two methods works - a plain class, no `pydantic_yaml` inheritance:

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

## A configurable engine, Pydantic-style

The built-in engines are themselves frozen `pydantic.BaseModel`s - you can follow the same
pattern for your own, getting validation, immutability, and a clean repr for free:

```python
import json
from io import IOBase
from typing import Any
from pydantic import BaseModel, ConfigDict

class JsonEngine(BaseModel):
    """A trivial custom engine: JSON is valid YAML, so this "just works"."""

    model_config = ConfigDict(frozen=True)

    indent: int | None = None

    def read(self, stream: IOBase) -> Any:
        return json.loads(stream.read())

    def write(self, stream: IOBase, model: BaseModel) -> None:
        stream.write(model.model_dump_json(indent=self.indent))
```

```python
from pydantic_yaml import to_yaml_str, parse_yaml_raw_as

engine = JsonEngine(indent=2)
dumped = to_yaml_str(model, engine=engine)
loaded = parse_yaml_raw_as(MyModel, dumped, engine=engine)
```

## Dumping "by hand"

Since `write(stream, model)` receives the actual Pydantic model instance - not a pre-serialized
value - your engine decides how to turn it into YAML. It doesn't have to go through JSON at all;
you could walk `type(model).model_fields` directly, call `model.model_dump(mode="python")`, or
use any lower-level `pydantic-core` API you like. This is exactly how the two built-in engines
work internally: each independently calls `model.model_dump_json()` and hands the result to its
own YAML library - nothing in `pydantic_yaml` forces JSON on a custom engine.
