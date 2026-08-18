"""YAML engine backed by the `ruamel.yaml` library.

This has been the default engine historically, but it is now an *optional* dependency (just
like `yamlrocks`, see `issue #338 <https://github.com/NowanIlfideme/pydantic-yaml/issues/338>`_):
install it with ``pip install pydantic-yaml[ruamel]``, then either pass ``engine="ruamel"``
explicitly or call `pydantic_yaml.set_default_engine("ruamel")`. If exactly one of the two
supported engines is installed, it's picked automatically; see
`pydantic_yaml._internals.v2.get_default_engine`.

This module is only imported when the `ruamel` engine is actually requested.

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
from textwrap import dedent
from typing import Any

from pydantic import BaseModel, RootModel
from pydantic.fields import FieldInfo

from pydantic_yaml._internals.comments import CommentsOptions, get_doc

try:
    from ruamel.yaml import YAML, CommentedMap, CommentedSeq
except ImportError as e:  # pragma: no cover
    raise ImportError(
        "The 'ruamel' engine requires the optional `ruamel.yaml` package. "
        "Install it with `pip install pydantic-yaml[ruamel]`."
    ) from e

__all__ = ["read_yaml_stream", "write_yaml_model"]


def as_yaml_comment(value: str | None) -> str | None:
    """Convert a value (e.g. docstring) into a YAML comment."""
    if value is None:
        return None
    lines = dedent(value.lstrip("\n").rstrip()).split("\n")
    return "\n".join([f"# {v}".strip() for v in lines])


def _add_descriptions(
    ystruct: CommentedMap | CommentedSeq,  # or other stuff...
    obj: BaseModel | Mapping | Sequence | Any,
    opts: CommentsOptions,
) -> None:
    """Add descriptions from the object to the yaml struct (modifying it).

    This will fail if `ystruct` and `obj` don't have the same structure.
    """
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


def read_yaml_stream(stream: Any) -> Any:
    """Read a YAML stream (str, bytes, or file-like object) into plain Python objects."""
    reader = YAML(typ="safe", pure=True)  # YAML 1.2 support
    return reader.load(stream)


def write_yaml_model(
    stream: IOBase,
    model: BaseModel,
    *,
    add_comments: CommentsOptions = False,
    default_flow_style: bool | None = None,
    indent: int | None = None,
    map_indent: int | None = None,
    sequence_indent: int | None = None,
    sequence_dash_offset: int | None = None,
    custom_yaml_writer: YAML | None = None,
    **json_kwargs: Any,
) -> None:
    """Write YAML model to the stream object, using `ruamel.yaml` as the backend.

    Parameters mirror `pydantic_yaml._internals.v2._write_yaml_model`; see that function's
    docstring.
    """
    if not isinstance(model, BaseModel):
        raise TypeError(f"Expected a Pydantic BaseModel, but got {type(model)}")
    json_val = model.model_dump_json(**json_kwargs)
    val = json.loads(json_val)
    # Allow setting custom writer
    if custom_yaml_writer is None:
        writer = YAML(typ="safe", pure=True)
    elif isinstance(custom_yaml_writer, YAML):
        writer = custom_yaml_writer
    else:
        raise TypeError(f"Please pass a YAML instance or subclass. Got {custom_yaml_writer!r}")
    # Set options
    if default_flow_style is not None:
        writer.default_flow_style = default_flow_style
    writer.indent(mapping=indent, sequence=indent, offset=indent)
    writer.indent(mapping=map_indent, sequence=sequence_indent, offset=sequence_dash_offset)
    # TODO: Configure writer further?
    if add_comments is False:
        writer.dump(val, stream)
    elif add_comments in (True, "fields-only", "models-only"):
        # We need to roundtrip!
        temp_stream = StringIO()
        writer.dump(val, temp_stream)
        rt_yaml = YAML(typ="rt", pure=True)
        ystruct = rt_yaml.load(temp_stream.getvalue())
        if isinstance(ystruct, CommentedMap | CommentedSeq):
            _add_descriptions(ystruct, obj=model, opts=add_comments)
            rt_yaml.dump(ystruct, stream)
        else:
            # Don't know what to do with this; just write the original value
            warnings.warn(
                "Failed to add comments to model; is not a map or sequence.",
                category=UserWarning,
            )
            writer.dump(val, stream)
