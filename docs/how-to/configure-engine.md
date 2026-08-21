# Choose and Configure a YAML Engine

`pydantic-yaml` reads/writes YAML through a pluggable **engine** object, passed as `engine=` to
`to_yaml_str`, `to_yaml_file`, `parse_yaml_raw_as`, and `parse_yaml_file_as`. All YAML-specific
configuration - formatting, comments, JSON-dump kwargs - lives on that engine object, not on the
functions themselves. See [Why a pluggable YAML engine?](../explanation/engine-design.md) for the
background, and [Write a custom YAML engine](write-custom-engine.md) if you want to bring your
own backend instead of the two built-ins.

## The two built-in engines

- [`YamlRocksEngine`](https://yaml.rocks) - backed by `yamlrocks`, a Rust engine that's YAML 1.2
  spec-compliant. **Recommended.**
- [`RuamelEngine`](https://yaml.readthedocs.io/) - backed by `ruamel.yaml`, the historical
  default.

If you don't pick one explicitly, whichever is installed is used automatically (preferring
`YamlRocksEngine` if both are) - see [Install pydantic-yaml](install.md).

## Pass a configured engine per call

```python
from pydantic_yaml import YamlRocksEngine, to_yaml_str, parse_yaml_raw_as

to_yaml_str(model, engine=YamlRocksEngine(sort_keys=True))
parse_yaml_raw_as(MyModel, yml, engine=YamlRocksEngine())
```

## Switch the default for the whole process

```python
from pydantic_yaml import RuamelEngine, set_default_engine

set_default_engine(RuamelEngine(indent=4))
```

After this, every call that doesn't pass its own `engine=` uses `RuamelEngine(indent=4)`.

There's no string-based engine selection (no `engine="yamlrocks"`, no `PYDANTIC_YAML_ENGINE` env
var) - always an actual engine object, so `engine=`/`set_default_engine()` work identically for
the built-ins and for anything you write yourself.

## Common formatting options

Both engines share these fields:

```python
from pydantic_yaml import RuamelEngine, to_yaml_str

to_yaml_str(model, engine=RuamelEngine(indent=4))          # wider indent
to_yaml_str(model, engine=RuamelEngine(default_flow_style=True))  # compact {a: 1, b: 2} style
to_yaml_str(model, engine=RuamelEngine(add_comments=True)) # docstrings/descriptions as comments
to_yaml_str(model, engine=RuamelEngine(sort_keys=True))    # alphabetize keys
```

Two defaults worth knowing, since they apply unconditionally on **both** engines and aren't
configurable: field declaration order is always preserved unless you opt into `sort_keys=True`,
and multiline strings always dump in block-literal (`|`) style.

Engines are immutable (`frozen` Pydantic models); derive a variant with `.model_copy(update=...)`
instead of mutating one:

```python
base_engine = RuamelEngine(indent=4)
with_comments = base_engine.model_copy(update={"add_comments": True})
```

Pass extra keyword arguments through to `model.model_dump_json()` (e.g. `exclude_none`,
`by_alias`) via `json_kwargs`:

```python
to_yaml_str(model, engine=RuamelEngine(json_kwargs={"exclude_none": True}))
```

## `RuamelEngine`-only options

Some formatting knobs only exist on `RuamelEngine`, since `yamlrocks` has no equivalent:

```python
# Independently-configurable map/sequence indent and dash offset:
to_yaml_str(model, engine=RuamelEngine(map_indent=9, sequence_indent=7))  # ... you monster.
```

You can also pass your own pre-built `ruamel.yaml.YAML` instance for full control:

```python
from ruamel.yaml import YAML
from pydantic_yaml import RuamelEngine, to_yaml_file

my_writer = YAML(typ="safe")
my_writer.default_flow_style = True
to_yaml_file("foo.yaml", model, engine=RuamelEngine(default_flow_style=None, writer=my_writer))
```

`default_flow_style=None` here means "leave `my_writer`'s own setting alone" - passing any
non-`None` value on the engine would override whatever the custom writer already has configured.

Passing a `RuamelEngine`-only field to `YamlRocksEngine` raises a `pydantic.ValidationError`
immediately (it's simply not a field on that model), rather than a runtime error deep inside a
dump call:

```python
from pydantic_yaml import YamlRocksEngine

YamlRocksEngine(map_indent=2)  # raises ValidationError: "map_indent" - Extra inputs are not permitted
```
