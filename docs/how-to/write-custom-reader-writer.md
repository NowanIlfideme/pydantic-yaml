# Write a Custom Reader/Writer

`pydantic-yaml`'s built-in backends are just implementations of the `YamlReader` and `YamlWriter`
protocols - any object with a `read(stream)` method works as a reader, and any object with a
`write(stream, model)` method works as a writer, no inheritance required. Bring your own YAML
library, or serialize by hand (bypassing JSON entirely) for full control. See
[Why pluggable readers and writers?](../explanation/engine-design.md) for the motivation, and
[Choose and configure readers/writers](configure-readers-writers.md) for using the built-ins.

## The protocols

```python
from io import IOBase
from typing import Any, Protocol, runtime_checkable
from pydantic import BaseModel

@runtime_checkable
class YamlReader(Protocol):
    def read(self, stream: IOBase) -> Any:
        """Read a YAML stream into plain Python objects, for TypeAdapter validation."""
        ...

@runtime_checkable
class YamlWriter(Protocol):
    def write(self, stream: IOBase, model: BaseModel) -> None:
        """Write `model` as YAML to `stream`, using this writer's own configuration."""
        ...
```

(These are the actual definitions, importable as `pydantic_yaml.YamlReader`/`YamlWriter` - shown
here for reference.) They're separate protocols on purpose: reading is a simple operation with
essentially no configuration, while writing has many independent formatting knobs, so an object
only needs to implement the half it actually does.

If you'd rather write one object that does both, implement both methods on it - it then
automatically satisfies `pydantic_yaml.YamlEngine`, a convenience protocol that's just the
intersection of the two:

```python
from pydantic_yaml import YamlEngine

@runtime_checkable
class YamlEngine(YamlReader, YamlWriter, Protocol):
    """Convenience protocol for an object that's both a YamlReader and a YamlWriter."""
```

You can pass such an object as `reader=` to the parsing functions and `writer=` to the dumping
functions - nothing requires you to split reading and writing into two separate objects, that's
just what the built-ins do internally.

## A minimal custom writer

Any object with the right method works - a plain class, no `pydantic_yaml` inheritance:

```python
from io import IOBase
from pydantic import BaseModel
from pydantic_yaml import to_yaml_str

class MyWriter:
    def write(self, stream: IOBase, model: BaseModel) -> None:
        ...  # serialize `model` to `stream`, however you like - JSON is not required

to_yaml_str(model, writer=MyWriter())
```

`isinstance(your_writer, YamlWriter)` works too (`YamlWriter` is a `@runtime_checkable`
`Protocol`), if you want to check conformance explicitly.

## A minimal custom reader

```python
from io import IOBase
from typing import Any
from pydantic_yaml import parse_yaml_raw_as

class MyReader:
    def read(self, stream: IOBase) -> Any:
        ...  # parse `stream` into plain Python objects

parse_yaml_raw_as(MyModel, yaml_text, reader=MyReader())
```

## A configurable writer, Pydantic-style

The built-in writers are themselves frozen `pydantic.BaseModel`s - you can follow the same
pattern for your own, getting validation, immutability, and a clean repr for free. Readers rarely
need configuration, but there's nothing stopping you from doing the same for one:

```python
import json
from io import IOBase
from typing import Any
from pydantic import BaseModel, ConfigDict

class JsonWriter(BaseModel):
    """A trivial custom writer: JSON is valid YAML, so this "just works"."""

    model_config = ConfigDict(frozen=True)

    indent: int | None = None

    def write(self, stream: IOBase, model: BaseModel) -> None:
        stream.write(model.model_dump_json(indent=self.indent))

class JsonReader(BaseModel):
    model_config = ConfigDict(frozen=True)

    def read(self, stream: IOBase) -> Any:
        return json.loads(stream.read())
```

```python
from pydantic_yaml import to_yaml_str, parse_yaml_raw_as

writer = JsonWriter(indent=2)
reader = JsonReader()
dumped = to_yaml_str(model, writer=writer)
loaded = parse_yaml_raw_as(MyModel, dumped, reader=reader)
```

Or, bundled into a single `YamlEngine`-conforming object if you'd rather keep the pair together:

```python
class JsonEngine(BaseModel):
    """Both read() and write() on one frozen model - satisfies YamlEngine."""

    model_config = ConfigDict(frozen=True)

    indent: int | None = None

    def read(self, stream: IOBase) -> Any:
        return json.loads(stream.read())

    def write(self, stream: IOBase, model: BaseModel) -> None:
        stream.write(model.model_dump_json(indent=self.indent))

engine = JsonEngine(indent=2)
dumped = to_yaml_str(model, writer=engine)
loaded = parse_yaml_raw_as(MyModel, dumped, reader=engine)
```

## Dumping "by hand"

Since `write(stream, model)` receives the actual Pydantic model instance - not a pre-serialized
value - your writer decides how to turn it into YAML. It doesn't have to go through JSON at all;
you could walk `type(model).model_fields` directly, call `model.model_dump(mode="python")`, or
use any lower-level `pydantic-core` API you like. This is exactly how the two built-in writers
work internally: each independently calls `model.model_dump_json()` and hands the result to its
own YAML library - nothing in `pydantic_yaml` forces JSON on a custom writer.
