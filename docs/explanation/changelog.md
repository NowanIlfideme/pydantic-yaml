# Breaking Changes Across Versions

This page collects the API changes worth knowing about if you're upgrading, newest first. For
day-to-day usage, see the [how-to guides](../how-to/install.md) instead - this page is about
*why* things changed, not how to use what's here today.

## The pluggable reader/writer redesign

`pydantic-yaml` moved from a fixed, `ruamel.yaml`-only backend to
[pluggable readers and writers](engine-design.md). This was a significant API change:

- `to_yaml_str`/`to_yaml_file` no longer accept `add_comments`, `indent`, `map_indent`,
  `sequence_indent`, `sequence_dash_offset`, `default_flow_style`, or `custom_yaml_writer`
  directly, and instead take a `writer=` object; `parse_yaml_raw_as`/`parse_yaml_file_as` take a
  `reader=` object. All backend-specific formatting config moved onto writer *instances* - e.g.
  `to_yaml_str(model, writer=RuamelWriter(indent=4))` instead of `to_yaml_str(model, indent=4)`.
  See [Choose and configure readers/writers](../how-to/configure-readers-writers.md).
- Reading and writing are separate protocols (`YamlReader`/`YamlWriter`), not one combined
  "engine" - a reader is a plain callable `reader(stream)` with no formatting config of its own,
  since parsing needs none. Both protocols are expressed via `__call__` rather than a named
  method, so a bare function satisfies either one - no class or inheritance required. See
  [Write a custom reader/writer](../how-to/write-custom-reader-writer.md).
- `reader=`/`writer=` never accept a string (`"ruamel"`/`"yamlrocks"`) - always an actual object.
  There's no `EngineName` type, and no `PYDANTIC_YAML_ENGINE` environment variable.
- `get_default_reader()`/`get_default_writer()` return `YamlReader`/`YamlWriter` objects, not
  strings; `set_default_reader()`/`set_default_writer()` take one each, tracked independently.
- `ruamel.yaml` is no longer a required dependency - `pydantic-yaml` needs *at least one* of
  `ruamel.yaml` or `yamlrocks` installed (via the `[ruamel]`/`[yamlrocks]`/`[all]` extras), and
  either suffices. See [Install pydantic-yaml](../how-to/install.md).
- Two default output changes apply to both built-in writers: field declaration order is
  preserved by default (previously alphabetized - pass `sort_keys=True` for the old behavior),
  and multiline strings dump in block-literal (`|`) style unconditionally (previously quoted
  with escaped `\n` on `RuamelWriter`).

See [Why pluggable readers and writers?](engine-design.md) for the reasoning behind each of
these.

## `pydantic-yaml` V1

The API for `pydantic-yaml` version 1.0.0 was greatly simplified from earlier releases, and
Pydantic v1 support was dropped entirely (`pydantic-yaml` now requires `pydantic>=2.8`).

### Mixin class removed

The `YamlModel`/`YamlModelMixin` base classes (which added `.yaml()` and updated `.parse_*()`
methods directly onto your models) are no longer available. Use the module-level functions
(`to_yaml_str`, `parse_yaml_raw_as`, etc.) instead - they work on any `BaseModel` without
requiring a special base class.

### Versioned models removed

The built-in "versioned model" feature (a `version` field validated against a min/max range) was
removed, since its usefulness for most users was questionable and it pulled in a `semver`
dependency for everyone. See
[Recover versioned models](../how-to/recover-versioned-models.md) for a drop-in replacement.
