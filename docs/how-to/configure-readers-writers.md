# Choose and Configure Readers/Writers

`pydantic-yaml` reads YAML through a **reader** object (`reader=`) and writes YAML through a
**writer** object (`writer=`) - passed to `parse_yaml_raw_as`/`parse_yaml_file_as` and
`to_yaml_str`/`to_yaml_file` respectively. They're deliberately separate: parsing is a simple,
largely unconfigurable operation, while writing has many independent formatting knobs, so a
writer carries configuration a reader never needs. See
[Why pluggable readers and writers?](../explanation/engine-design.md) for the background, and
[Write a custom reader/writer](write-custom-reader-writer.md) if you want to bring your own
backend instead of the two built-ins.

## The two built-in backends

- [`yamlrocks`](https://yaml.rocks) (`YamlRocksReader`/`YamlRocksWriter`) - a Rust engine that's
  YAML 1.2 spec-compliant. **Recommended.**
- [`ruamel.yaml`](https://yaml.readthedocs.io/) (`RuamelReader`/`RuamelWriter`) - the historical
  default.

If you don't pick one explicitly, whichever is installed is used automatically (preferring
`yamlrocks` if both are) - see [Install pydantic-yaml](install.md).

## Pass a configured reader/writer per call

```python
from pydantic_yaml import YamlRocksReader, YamlRocksWriter, to_yaml_str, parse_yaml_raw_as

to_yaml_str(model, writer=YamlRocksWriter(sort_keys=True))
parse_yaml_raw_as(MyModel, yml, reader=YamlRocksReader())
```

## Switch the defaults for the whole process

```python
from pydantic_yaml import RuamelReader, RuamelWriter, set_default_reader, set_default_writer

set_default_reader(RuamelReader())
set_default_writer(RuamelWriter(indent=4))
```

After this, every call that doesn't pass its own `reader=`/`writer=` uses these. The two
defaults are tracked independently - you can mix backends (e.g. read with one library, write
with another) if you ever need to, though normally you'll set both to the same backend.

There's no string-based selection (no `reader="yamlrocks"`, no `PYDANTIC_YAML_ENGINE` env var) -
always an actual object, so `reader=`/`writer=`/`set_default_reader()`/`set_default_writer()`
work identically for the built-ins and for anything you write yourself.

## Common writer options

Both writers share these fields:

```python
from pydantic_yaml import RuamelWriter, to_yaml_str

to_yaml_str(model, writer=RuamelWriter(indent=4))          # wider indent
to_yaml_str(model, writer=RuamelWriter(default_flow_style=True))  # compact {a: 1, b: 2} style
to_yaml_str(model, writer=RuamelWriter(add_comments=True)) # docstrings/descriptions as comments
to_yaml_str(model, writer=RuamelWriter(sort_keys=True))    # alphabetize keys
```

Two defaults worth knowing, since they apply unconditionally on **both** writers and aren't
configurable: field declaration order is always preserved unless you opt into `sort_keys=True`,
and multiline strings always dump in block-literal (`|`) style.

Writers are immutable (`frozen` Pydantic models); derive a variant with `.model_copy(update=...)`
instead of mutating one:

```python
base_writer = RuamelWriter(indent=4)
with_comments = base_writer.model_copy(update={"add_comments": True})
```

Pass extra keyword arguments through to `model.model_dump_json()` (e.g. `exclude_none`,
`by_alias`) via `json_kwargs`:

```python
to_yaml_str(model, writer=RuamelWriter(json_kwargs={"exclude_none": True}))
```

The readers, by contrast, take no configuration at all today - `RuamelReader()`/
`YamlRocksReader()` are the only ways to construct them.

## `RuamelWriter`-only options

Some formatting knobs only exist on `RuamelWriter`, since `yamlrocks` has no equivalent:

```python
# Independently-configurable map/sequence indent and dash offset:
to_yaml_str(model, writer=RuamelWriter(map_indent=9, sequence_indent=7))  # ... you monster.
```

You can also pass your own pre-built `ruamel.yaml.YAML` instance for full control:

```python
from ruamel.yaml import YAML
from pydantic_yaml import RuamelWriter, to_yaml_file

my_writer = YAML(typ="safe")
my_writer.default_flow_style = True
to_yaml_file("foo.yaml", model, writer=RuamelWriter(default_flow_style=None, writer=my_writer))
```

`default_flow_style=None` here means "leave `my_writer`'s own setting alone" - passing any
non-`None` value would override whatever the custom writer already has configured.

Passing a `RuamelWriter`-only field to `YamlRocksWriter` raises a `pydantic.ValidationError`
immediately (it's simply not a field on that model), rather than a runtime error deep inside a
dump call:

```python
from pydantic_yaml import YamlRocksWriter

YamlRocksWriter(map_indent=2)  # raises ValidationError: "map_indent" - Extra inputs are not permitted
```
