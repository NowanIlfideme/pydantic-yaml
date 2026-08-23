# Why Pluggable Readers and Writers?

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
works fine for many), and it wouldn't have actually solved #217 or #34 - both backends had the
same field-sorting default, and only one of them handled multiline strings well. Picking between
two hardcoded backends via a string (`engine="ruamel"` vs `engine="yamlrocks"`) also didn't scale
to a genuine ask buried in the same milestone: **the ability to write a custom backend entirely**,
including one that doesn't go through JSON at all ("dumping by hand").

## The actual design

`pydantic-yaml` reads YAML through a `YamlReader` object (callable as `reader(stream)`) and
writes YAML through a `YamlWriter` object (callable as `writer(stream, model)`) - two separate,
`@runtime_checkable` `Protocol`s expressed via `__call__`, passed as `reader=`/`writer=`. A few
decisions shaped this:

**`typing.Protocol`, not an abstract base class.** A custom reader or writer needs zero dependency
on `pydantic_yaml` - no import, no inheritance. `@runtime_checkable` still lets you write
`isinstance(your_writer, YamlWriter)` if you want an explicit conformance check.

**`__call__`, not a named method.** Early designs used `read()`/`write()` methods, which meant
only class instances (with the right method name) could plug in. Expressing both protocols as
`__call__` means a bare function - `def my_writer(stream, model): ...` - satisfies `YamlWriter`
automatically, with nothing to inherit and no method name to remember. The tradeoff: since an
object's `__call__` can only have one signature, a single object can't cleanly implement both
`YamlReader` and `YamlWriter` at once (unlike separate `read()`/`write()` methods, which could
coexist on one class) - a reader and a writer are always a *pair* of callables, matching how the
built-ins are structured (`RuamelReader`/`RuamelWriter`, not one `RuamelEngine`).

**Reading and writing are separate protocols, not one combined "engine."** Parsing YAML is a
single, largely unconfigurable operation - `RuamelReader()`/`YamlRocksReader()` take no fields at
all. Writing has many independent formatting knobs (indentation, key sorting, comments, flow
style, ...). Bundling both into one object meant every reader silently carried a pile of
write-only fields it never used, and reading had no way to reject a writer-only setting that
didn't apply to it. Splitting them means `RuamelReader` and `RuamelWriter` each only have the
fields relevant to what they actually do.

**Readers/writers own their configuration.** Formatting options, `add_comments`, and JSON-dump
kwargs used to live on `to_yaml_str`/`to_yaml_file` themselves as flat keyword arguments - which
meant every option had to make sense for *every* backend, or be silently ignored, or raise at call
time. Instead, `RuamelWriter`/`YamlRocksWriter` are frozen `pydantic.BaseModel`s that each declare
only the fields they can actually honor. `YamlRocksWriter` simply has no `map_indent` field,
because `yamlrocks` has no equivalent knob - passing one raises a `pydantic.ValidationError` at
construction time, not a `NotImplementedError` buried inside a dump call. See
[Choose and configure readers/writers](../how-to/configure-readers-writers.md).

**No string-based selection.** Early designs let you write `engine="yamlrocks"` and looked up a
name in a registry. That doesn't generalize to arbitrary custom backends without adding a
registration API purely for the sake of strings. `reader=`/`writer=` and
`set_default_reader()`/`set_default_writer()` always take an actual object - a built-in,
pre-configured however you like, or your own. See
[Write a custom reader/writer](../how-to/write-custom-reader-writer.md).

**#217 and #34 became defaults, not options.** Once formatting lived on the writer itself, both
fixes were natural: field declaration order is preserved by default on both writers (`sort_keys`
opts back into alphabetizing), and multiline strings dump in block-literal style
unconditionally - `yamlrocks` already did this automatically with no way to disable it, so
`RuamelWriter` was made to match rather than exposing a toggle only one backend could honor.

## Known cross-engine differences

Both built-in backends are extensively tested against each other, but a couple of cosmetic
differences remain, inherent to how the two underlying libraries work:

- **Comment placement with nested descriptions.** `RuamelWriter` sometimes drops a nested
  model's docstring when `add_comments=True` and that same field also has its own description -
  a known `ruamel.yaml` inconsistency. `YamlRocksWriter` includes both.
- **Comments on a multiline field.** A field's own description comment can't sit on the same
  line as a block-literal (`|`) value, since the value spans multiple lines. Both writers dump
  it on a dangling, oddly-indented line right after the value instead - identical behavior on
  both, harmless (the data still round-trips correctly), just not pretty.
- **Multiline strings under `default_flow_style=True`.** A block-literal scalar can't exist
  inside flow style at all (`|` is a block-only construct) - both writers consistently fall back
  to a quoted, escaped string for that one value instead.
