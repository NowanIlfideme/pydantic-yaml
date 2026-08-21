# Why a Pluggable YAML Engine?

## The problem with `ruamel.yaml`

`pydantic-yaml` originally used [`ruamel.yaml`](https://yaml.readthedocs.io/) as its only YAML
backend. Over time, several problems became hard to ignore (tracked in
[issue #338](https://github.com/NowanIlfideme/pydantic-yaml/issues/338)):

- `ruamel.yaml` doesn't pass the [yaml-test-suite](https://github.com/yaml/yaml-test-suite),
  per a [SourceForge issue](https://sourceforge.net/p/ruamel-yaml/tickets/570/) against the
  project.
- Comment handling has been inconsistent across `ruamel.yaml` versions, and a chore to work
  around.
- The library has a history of breaking compatibility across *minor* version releases.

Alongside that, two other longstanding feature requests were part of the same "Version 2 - YAML
Customization" milestone:

- [#217](https://github.com/NowanIlfideme/pydantic-yaml/issues/217) - dumping alphabetized
  fields instead of preserving a model's declared field order (surprising, undocumented
  behavior inherited from `ruamel.yaml`'s own default).
- [#34](https://github.com/NowanIlfideme/pydantic-yaml/issues/34) - no way to get multiline
  strings dumped in YAML's block-literal (`|`) style instead of a quoted string with escaped
  `\n` characters.

## Why not just swap the library?

The first idea was simple: replace `ruamel.yaml` with something better. [`yamlrocks`](https://yaml.rocks) -
a Rust-backed engine that's YAML 1.2 spec-compliant and does pass the yaml-test-suite - is exactly
that "something better," and it's the recommended default today.

But swapping libraries wholesale would have been risky for existing users (`ruamel.yaml` still
works fine for many), and it wouldn't have actually solved #217 or #34 - both engines had the
same field-sorting default, and only one of them handled multiline strings well. Picking between
two hardcoded backends via a string (`engine="ruamel"` vs `engine="yamlrocks"`) also didn't scale
to a genuine ask buried in the same milestone: **the ability to write a custom engine entirely**,
including one that doesn't go through JSON at all ("dumping by hand").

## The actual design

`pydantic-yaml` reads/writes YAML through a `YamlEngine` object - anything with `read(stream)`
and `write(stream, model)` methods. A few decisions shaped this:

**`typing.Protocol`, not an abstract base class.** A custom engine needs zero dependency on
`pydantic_yaml` - no import, no inheritance. `@runtime_checkable` still lets you write
`isinstance(your_engine, YamlEngine)` if you want an explicit conformance check.

**Engines own their configuration.** Formatting options, `add_comments`, and JSON-dump kwargs
used to live on `to_yaml_str`/`to_yaml_file` themselves as flat keyword arguments - which meant
every option had to make sense for *every* engine, or be silently ignored, or raise at call time.
Instead, `RuamelEngine`/`YamlRocksEngine` are frozen `pydantic.BaseModel`s that each declare only
the fields they can actually honor. `YamlRocksEngine` simply has no `map_indent` field, because
`yamlrocks` has no equivalent knob - passing one raises a `pydantic.ValidationError` at
construction time, not a `NotImplementedError` buried inside a dump call. See
[Choose and configure a YAML engine](../how-to/configure-engine.md).

**No string-based selection.** Early designs let you write `engine="yamlrocks"` and looked up a
name in a registry. That doesn't generalize to arbitrary custom engines without adding a
registration API purely for the sake of strings. `engine=` and `set_default_engine()` always take
an actual engine *object* - a built-in, pre-configured however you like, or your own. See
[Write a custom YAML engine](../how-to/write-custom-engine.md).

**#217 and #34 became defaults, not options.** Once formatting lived on the engine itself, both
fixes were natural: field declaration order is preserved by default on both engines (`sort_keys`
opts back into alphabetizing), and multiline strings dump in block-literal style
unconditionally - `yamlrocks` already did this automatically with no way to disable it, so
`RuamelEngine` was made to match rather than exposing a toggle only one engine could honor.

## Known cross-engine differences

Both built-in engines are extensively tested against each other, but a couple of cosmetic
differences remain, inherent to how the two underlying libraries work:

- **Comment placement with nested descriptions.** `RuamelEngine` sometimes drops a nested
  model's docstring when `add_comments=True` and that same field also has its own description -
  a known `ruamel.yaml` inconsistency. `YamlRocksEngine` includes both.
- **Comments on a multiline field.** A field's own description comment can't sit on the same
  line as a block-literal (`|`) value, since the value spans multiple lines. Both engines dump
  it on a dangling, oddly-indented line right after the value instead - identical behavior on
  both, harmless (the data still round-trips correctly), just not pretty.
- **Multiline strings under `default_flow_style=True`.** A block-literal scalar can't exist
  inside flow style at all (`|` is a block-only construct) - both engines consistently fall back
  to a quoted, escaped string for that one value instead.
