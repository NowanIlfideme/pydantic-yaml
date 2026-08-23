"""YAML reader/writer backed by the `ruamel.yaml` library.

This has been the default engine historically, but it is now an *optional* dependency (just
like `yamlrocks`, see `issue #338 <https://github.com/NowanIlfideme/pydantic-yaml/issues/338>`_):
install it with ``pip install pydantic-yaml[ruamel]``.

Importing this module never requires `ruamel.yaml` to be installed - only constructing a
`RuamelReader`/`RuamelWriter` (or calling one) does.

Reading and writing are deliberately separate classes: parsing YAML is a simple, mostly
unconfigurable operation, while writing has many independent formatting knobs - bundling both
into one class meant `read()` carried a pile of fields (`indent`, `add_comments`, ...) it never
looked at.

See Also
--------
Roundtrip comments with ruamel.yaml
    https://yaml.readthedocs.io/en/latest/detail.html#round-trip-including-comments
    Currently, it's not possible to round-trip comments in `pydantic-yaml`.
    If you need to keep comments, you'll have to have parallel updating and validation.
"""

from __future__ import annotations

import json
import warnings
from collections.abc import Mapping, Sequence
from io import IOBase, StringIO
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, RootModel, model_validator
from pydantic.fields import FieldInfo

from pydantic_yaml._internals.comments import CommentsOptions, get_doc

__all__ = ["RuamelReader", "RuamelWriter"]


class RuamelReader(BaseModel):
    """YAML reader backed by `ruamel.yaml`.

    Optional dependency: install with `pip install pydantic-yaml[ruamel]`.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    @model_validator(mode="after")
    def _check_available(self) -> RuamelReader:
        try:
            import ruamel.yaml  # noqa: F401
        except ImportError as e:
            raise ImportError(
                "The 'ruamel' reader requires the optional `ruamel.yaml` package. "
                "Install it with `pip install pydantic-yaml[ruamel]`."
            ) from e
        return self

    def __call__(self, stream: IOBase) -> Any:
        """Read a YAML stream (str, bytes, or file-like object) into plain Python objects."""
        from ruamel.yaml import YAML

        reader = YAML(typ="safe", pure=True)  # YAML 1.2 support
        return reader.load(stream)


_literal_scalarstring_registered = False


def _ensure_literal_scalarstring_registered() -> None:
    """Register `LiteralScalarString` with `SafeRepresenter`, once per process.

    Only `RoundTripRepresenter` (`typ="rt"`) has this registered by default; `SafeRepresenter`
    (`typ="safe"`, what `RuamelWriter` uses) does not, so wrapping a value in
    `LiteralScalarString` would otherwise have no effect on it. Representer dispatch is by
    `type(data)` regardless of `typ=`, so this single, process-wide registration makes
    `typ="safe"` writers honor it too (verified empirically) - mirrors how ruamel itself
    registers every builtin type at module scope in `ruamel.yaml.representer`.
    """
    global _literal_scalarstring_registered
    if _literal_scalarstring_registered:
        return
    from ruamel.yaml.representer import RoundTripRepresenter, SafeRepresenter
    from ruamel.yaml.scalarstring import LiteralScalarString

    SafeRepresenter.add_representer(
        LiteralScalarString, RoundTripRepresenter.represent_literal_scalarstring
    )
    _literal_scalarstring_registered = True


def _wrap_multiline_strings(val: Any) -> Any:
    r"""Recursively wrap `str` values containing `"\n"` in `LiteralScalarString`.

    Operates on the plain JSON-derived structure from `json.loads(model.model_dump_json(...))`,
    so only `dict | list | str | int | float | bool | None` are possible. Only mapping *values*
    and sequence *items* are wrapped, not mapping keys. Pure function (returns a new structure).
    """
    from ruamel.yaml.scalarstring import LiteralScalarString

    if isinstance(val, str):
        return LiteralScalarString(val) if "\n" in val else val
    if isinstance(val, dict):
        return {k: _wrap_multiline_strings(v) for k, v in val.items()}
    if isinstance(val, list):
        return [_wrap_multiline_strings(v) for v in val]
    return val


def _add_descriptions(
    ystruct: Any,  # CommentedMap | CommentedSeq, or other stuff...
    obj: BaseModel | Mapping | Sequence | Any,
    opts: CommentsOptions,
) -> None:
    """Add descriptions from the object to the yaml struct (modifying it).

    This will fail if `ystruct` and `obj` don't have the same structure.
    """
    from ruamel.yaml import CommentedMap, CommentedSeq

    # Add top-level comment
    top_lvl = get_doc(obj, opts=opts)
    if top_lvl is not None:
        try:
            indent = ystruct.lc.col
        except Exception:
            indent = 0
        ystruct.yaml_set_start_comment(top_lvl, indent=indent)

    if isinstance(obj, BaseModel):
        if obj.__pydantic_root_model__:
            # RootModel should probably work
            assert isinstance(obj, RootModel), "Model incorrectly set as RootModel."
            obj = obj.root

    if isinstance(obj, BaseModel):
        # Add field information
        flds: dict[str, FieldInfo]

        if isinstance(obj, BaseModel):
            flds = type(obj).model_fields

        for fld_name, fld_info in flds.items():
            if not isinstance(ystruct, CommentedMap):
                raise NotImplementedError("Can't add field descriptions to non-mapping YAML structures.")
            if fld_name in ystruct.keys():
                # Add field description (if any/allowed)
                fld_desc = get_doc(fld_info, opts=opts)
                if fld_desc is not None:
                    # Convert multi-line descriptions to single-line by replacing newlines with spaces
                    fld_desc_single = fld_desc.replace("\n", " ").strip()
                    ystruct.yaml_add_eol_comment(fld_desc_single, key=fld_name)

                # Recurse into fields
                fld_obj = getattr(obj, fld_name, None)
                if isinstance(fld_obj, BaseModel | Sequence | Mapping):
                    _add_descriptions(ystruct[fld_name], fld_obj, opts=opts)
                # otherwise - no additional descriptions
    elif isinstance(obj, Sequence) and isinstance(ystruct, CommentedSeq):
        # Recurse into parts of the sequence; needed in cases of `list[dict[str, MyModel]]` and such
        for i, sub_obj in enumerate(obj):
            _add_descriptions(ystruct[i], sub_obj, opts=opts)
    elif isinstance(obj, Mapping) and isinstance(ystruct, CommentedMap):
        for key, sub_obj in obj.items():
            _add_descriptions(ystruct[key], sub_obj, opts=opts)


class RuamelWriter(BaseModel):
    """YAML writer backed by `ruamel.yaml`.

    Optional dependency: install with `pip install pydantic-yaml[ruamel]`. Instances are
    immutable (`frozen`); use `.model_copy(update={...})` to derive a variant.
    """

    model_config = ConfigDict(frozen=True, arbitrary_types_allowed=True, extra="forbid")

    add_comments: CommentsOptions = False
    """Whether to add comments to the output YAML using model docstrings and/or field
    descriptions."""

    default_flow_style: bool | None = False
    """Whether to use "flow style" (more compact). `False` (the default) means block style -
    ruamel's own untouched default is actually flow style, so this is an intentional override.
    `None` leaves whatever `writer` (or a freshly constructed one) already has untouched."""

    sort_keys: bool | None = False
    """Whether to alphabetize mapping keys. `False` (the default) preserves field declaration
    order. `None` leaves `writer`'s own setting untouched."""

    indent: int | None = None
    map_indent: int | None = None
    sequence_indent: int | None = None
    sequence_dash_offset: int | None = None
    """General and specific indent values; `None` leaves the default/writer's own setting."""

    writer: Any = None
    """An optional pre-built `ruamel.yaml.YAML` instance to use (and mutate) instead of
    constructing a fresh one. Typed `Any` so importing/defining this class never requires
    `ruamel.yaml` to be installed; validated to be a `YAML` instance when actually used."""

    json_kwargs: dict[str, Any] = Field(default_factory=dict)
    """Extra keyword arguments forwarded to `model.model_dump_json(**json_kwargs)`."""

    @model_validator(mode="after")
    def _check_available(self) -> RuamelWriter:
        try:
            from ruamel.yaml import YAML
        except ImportError as e:
            raise ImportError(
                "The 'ruamel' writer requires the optional `ruamel.yaml` package. "
                "Install it with `pip install pydantic-yaml[ruamel]`."
            ) from e
        if self.writer is not None and not isinstance(self.writer, YAML):
            raise TypeError(f"`writer` must be a ruamel.yaml.YAML instance, got {self.writer!r}")
        _ensure_literal_scalarstring_registered()
        return self

    def __call__(self, stream: IOBase, model: BaseModel) -> None:
        """Write `model` as YAML to `stream`, using this writer's own configuration."""
        from ruamel.yaml import YAML, CommentedMap, CommentedSeq

        if not isinstance(model, BaseModel):
            raise TypeError(f"Expected a Pydantic BaseModel, but got {type(model)}")
        json_val = model.model_dump_json(**self.json_kwargs)
        val = json.loads(json_val)
        val = _wrap_multiline_strings(val)

        writer = self.writer if self.writer is not None else YAML(typ="safe", pure=True)
        if self.default_flow_style is not None:
            writer.default_flow_style = self.default_flow_style
        if self.sort_keys is not None:
            writer.sort_base_mapping_type_on_output = self.sort_keys
        writer.indent(mapping=self.indent, sequence=self.indent, offset=self.indent)
        writer.indent(
            mapping=self.map_indent, sequence=self.sequence_indent, offset=self.sequence_dash_offset
        )

        if self.add_comments is False:
            writer.dump(val, stream)
        elif self.add_comments in (True, "fields-only", "models-only"):
            # We need to roundtrip!
            temp_stream = StringIO()
            writer.dump(val, temp_stream)
            rt_yaml = YAML(typ="rt", pure=True)
            ystruct = rt_yaml.load(temp_stream.getvalue())
            if isinstance(ystruct, CommentedMap | CommentedSeq):
                _add_descriptions(ystruct, obj=model, opts=self.add_comments)
                rt_yaml.dump(ystruct, stream)
            else:
                # Don't know what to do with this; just write the original value
                warnings.warn(
                    "Failed to add comments to model; is not a map or sequence.",
                    category=UserWarning,
                )
                writer.dump(val, stream)
        else:
            raise ValueError(f"Invalid `add_comments` value: {self.add_comments!r}")
