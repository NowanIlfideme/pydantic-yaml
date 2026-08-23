# Write a Custom Reader/Writer

`pydantic-yaml`'s built-in backends are just implementations of the `YamlReader` and `YamlWriter`
protocols - any *callable* `reader(stream) -> Any` works as a reader, and any callable
`writer(stream, model) -> None` works as a writer. Because both protocols are expressed via
`__call__` rather than a named method, a plain function works just as well as a class instance -
no inheritance, and no dedicated method name, required. Bring your own YAML library, or serialize
by hand (bypassing JSON entirely) for full control. See
[Why pluggable readers and writers?](../explanation/engine-design.md) for the motivation, and
[Choose and configure readers/writers](configure-readers-writers.md) for using the built-ins.

## The protocols

```python
from io import IOBase
from typing import Any, Protocol, runtime_checkable
from pydantic import BaseModel

@runtime_checkable
class YamlReader(Protocol):
    def __call__(self, stream: IOBase) -> Any:
        """Read a YAML stream into plain Python objects, for TypeAdapter validation."""
        ...

@runtime_checkable
class YamlWriter(Protocol):
    def __call__(self, stream: IOBase, model: BaseModel) -> None:
        """Write `model` as YAML to `stream`, using this writer's own configuration."""
        ...
```

(These are the actual definitions, importable as `pydantic_yaml.YamlReader`/`YamlWriter` - shown
here for reference.) They're separate protocols on purpose: reading is a simple operation with
essentially no configuration, while writing has many independent formatting knobs, so an object
only needs to implement the half it actually does.

Because a plain function has a `__call__` slot too, any function with the right signature already
satisfies these protocols - `isinstance(some_function, YamlWriter)` is `True` as long as it's
callable, no special decoration needed. This is also why there's no separate "combined engine"
protocol: an object's `__call__` can only have one signature, so a single object can't cleanly
implement both `YamlReader` and `YamlWriter` at once - pair a reader function/object with a
writer function/object instead (see the built-ins, which do exactly this).

## A minimal custom writer

Any callable with the right signature works - including a bare function:

```python
from io import IOBase
from pydantic import BaseModel
from pydantic_yaml import to_yaml_str

def my_writer(stream: IOBase, model: BaseModel) -> None:
    ...  # serialize `model` to `stream`, however you like - JSON is not required

to_yaml_str(model, writer=my_writer)
```

`isinstance(your_writer, YamlWriter)` works too (`YamlWriter` is a `@runtime_checkable`
`Protocol`), if you want to check conformance explicitly - though since it only checks for
`__call__`, it can't tell a writer function apart from a reader function by signature; it just
confirms *something* is callable.

## A minimal custom reader

```python
from io import IOBase
from typing import Any
from pydantic_yaml import parse_yaml_raw_as

def my_reader(stream: IOBase) -> Any:
    ...  # parse `stream` into plain Python objects

parse_yaml_raw_as(MyModel, yaml_text, reader=my_reader)
```

## A configurable writer, Pydantic-style

A plain function has no way to carry configuration, so if you need options, use a callable
object instead. The built-in writers are themselves frozen `pydantic.BaseModel`s with `__call__`
defined - you can follow the same pattern for your own, getting validation, immutability, and a
clean repr for free. Readers rarely need configuration, but there's nothing stopping you from
doing the same for one:

```python
import json
from io import IOBase
from typing import Any
from pydantic import BaseModel, ConfigDict

class JsonWriter(BaseModel):
    """A trivial custom writer: JSON is valid YAML, so this "just works"."""

    model_config = ConfigDict(frozen=True)

    indent: int | None = None

    def __call__(self, stream: IOBase, model: BaseModel) -> None:
        stream.write(model.model_dump_json(indent=self.indent))

class JsonReader(BaseModel):
    model_config = ConfigDict(frozen=True)

    def __call__(self, stream: IOBase) -> Any:
        return json.loads(stream.read())
```

```python
from pydantic_yaml import to_yaml_str, parse_yaml_raw_as

writer = JsonWriter(indent=2)
reader = JsonReader()
dumped = to_yaml_str(model, writer=writer)
loaded = parse_yaml_raw_as(MyModel, dumped, reader=reader)
```

## Dumping "by hand"

Since a writer receives the actual Pydantic model instance - not a pre-serialized value - it
decides how to turn it into YAML. It doesn't have to go through JSON at all; you could walk
`type(model).model_fields` directly, call `model.model_dump(mode="python")`, or use any
lower-level `pydantic-core` API you like. This is exactly how the two built-in writers work
internally: each independently calls `model.model_dump_json()` and hands the result to its own
YAML library - nothing in `pydantic_yaml` forces JSON on a custom writer.
