"""YAML engine backed by the `yamlrocks` library.

`yamlrocks` is a Rust-based YAML 1.2 implementation that passes the yaml-test-suite
(unlike `ruamel.yaml`, see
`issue #338 <https://github.com/NowanIlfideme/pydantic-yaml/issues/338>`_).
It is an *optional* dependency: install it with ``pip install pydantic-yaml[yamlrocks]``,
then either pass ``engine="yamlrocks"`` explicitly or call
`pydantic_yaml.set_default_engine("yamlrocks")`.

This module is only imported when the `yamlrocks` engine is actually requested.
"""

from __future__ import annotations

import json
import warnings
from collections.abc import Mapping, Sequence
from io import IOBase
from typing import Any

from pydantic import BaseModel, RootModel

from pydantic_yaml._internals.comments import CommentsOptions, get_doc

try:
    import yamlrocks as yr
except ImportError as e:  # pragma: no cover
    raise ImportError(
        "The 'yamlrocks' engine requires the optional `yamlrocks` package. "
        "Install it with `pip install pydantic-yaml[yamlrocks]`."
    ) from e

__all__ = ["read_yaml_stream", "write_yaml_model"]


def _child_keys(node: yr.YAMLRocksNode) -> list[Any]:
    """Get the ordered keys/indices of a mapping/sequence node, or `[]` for anything else."""
    val = node.value
    if isinstance(val, dict):
        return list(val.keys())
    if isinstance(val, list):
        return list(range(len(val)))
    return []


def _add_descriptions(node: yr.YAMLRocksNode, obj: Any, opts: CommentsOptions) -> None:
    """Add descriptions from `obj` onto the round-tripped `node` tree (mutates in place).

    Mirrors `pydantic_yaml._internals.v2._add_descriptions`, adapted to the yamlrocks node API:
    a "start comment" is emitted by setting `comment_before` on the *first child* of a mapping
    (setting it on the node itself would place the comment above that node's own key/line),
    while per-field descriptions become trailing (`comment`) comments on the field's value node.
    """
    top_lvl = get_doc(obj, opts=opts)
    if top_lvl is not None:
        start_keys = _child_keys(node)
        if start_keys:
            node[start_keys[0]].comment_before = top_lvl

    if isinstance(obj, BaseModel) and obj.__pydantic_root_model__:
        assert isinstance(obj, RootModel), "Model incorrectly set as RootModel."
        obj = obj.root

    if isinstance(obj, BaseModel):
        flds = type(obj).model_fields
        fld_keys = set(_child_keys(node))
        for fld_name, fld_info in flds.items():
            if fld_name not in fld_keys:
                continue
            fld_desc = get_doc(fld_info, opts=opts)
            if fld_desc is not None:
                fld_desc_single = fld_desc.replace("\n", " ").strip()
                node[fld_name].comment = fld_desc_single

            fld_obj = getattr(obj, fld_name, None)
            if isinstance(fld_obj, BaseModel | Mapping) or (
                isinstance(fld_obj, Sequence) and not isinstance(fld_obj, str | bytes)
            ):
                _add_descriptions(node[fld_name], fld_obj, opts=opts)
    elif isinstance(obj, Sequence) and not isinstance(obj, str | bytes):
        n_children = len(_child_keys(node))
        for i, sub_obj in enumerate(obj):
            if i < n_children:
                _add_descriptions(node[i], sub_obj, opts=opts)
    elif isinstance(obj, Mapping):
        map_keys = set(_child_keys(node))
        for key, sub_obj in obj.items():
            if key in map_keys:
                _add_descriptions(node[key], sub_obj, opts=opts)


def _resolve_option(
    *,
    default_flow_style: bool | None,
    indent: int | None,
    map_indent: int | None,
    sequence_indent: int | None,
    sequence_dash_offset: int | None,
) -> int:
    """Translate the ruamel-style formatting kwargs into `yamlrocks` `OPT_*` flags.

    `yamlrocks` only offers a single 2-or-4-space indent (applied uniformly to maps and
    sequences) plus an indentless-sequences toggle, unlike ruamel's fully independent
    `indent`/`map_indent`/`sequence_indent`/`sequence_dash_offset`. Combinations that aren't
    representable raise `NotImplementedError` pointing at `engine="ruamel"` instead of silently
    dropping the setting.
    """
    unsupported = [
        name
        for name, val in [
            ("map_indent", map_indent),
            ("sequence_indent", sequence_indent),
        ]
        if val is not None and val != indent
    ]
    if sequence_dash_offset not in (None, 0):
        unsupported.append("sequence_dash_offset")
    if unsupported:
        raise NotImplementedError(
            f"The 'yamlrocks' engine does not support {', '.join(unsupported)}; "
            "use a single `indent` of 2 or 4 (applied to both maps and sequences), "
            "or switch to `engine='ruamel'` for finer-grained control."
        )
    if indent is None:
        # Mirrors ruamel.yaml's default (offset=0): sequence dashes aren't further indented.
        option = yr.OPT_INDENT_2 | yr.OPT_INDENTLESS_SEQUENCES
    elif indent == 2:
        option = yr.OPT_INDENT_2
    elif indent == 4:
        option = yr.OPT_INDENT_4
    else:
        raise NotImplementedError(
            f"The 'yamlrocks' engine only supports `indent` values of 2 or 4, got {indent!r}; "
            "switch to `engine='ruamel'` for finer-grained control."
        )
    # ruamel's `YAML(typ="safe")` (used by the "ruamel" engine) sorts mapping keys by default;
    # match that here so switching engines doesn't silently reorder output.
    option |= yr.OPT_SORT_KEYS
    if default_flow_style:
        option |= yr.OPT_FLOW_STYLE
    return option


def read_yaml_stream(stream: Any) -> Any:
    """Read a YAML stream (str, bytes, or file-like object) into plain Python objects."""
    return yr.load(stream)


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
    **json_kwargs: Any,
) -> None:
    """Write YAML model to the stream object, using `yamlrocks` as the backend.

    Parameters mirror `pydantic_yaml._internals.v2._write_yaml_model`; see that function's
    docstring. `custom_yaml_writer` is not accepted here since it is specific to the ruamel
    engine - it is rejected by the caller before this function is invoked.
    """
    if not isinstance(model, BaseModel):
        raise TypeError(f"Expected a Pydantic BaseModel, but got {type(model)}")
    json_val = model.model_dump_json(**json_kwargs)
    val = json.loads(json_val)

    option = _resolve_option(
        default_flow_style=default_flow_style,
        indent=indent,
        map_indent=map_indent,
        sequence_indent=sequence_indent,
        sequence_dash_offset=sequence_dash_offset,
    )

    if add_comments is False:
        yr.dump(val, stream, option=option)
        return
    if add_comments not in (True, "fields-only", "models-only"):
        raise ValueError(f"Invalid `add_comments` value: {add_comments!r}")

    # We need to roundtrip, same as the ruamel engine does.
    raw = yr.dumps(val, option=option)
    doc = yr.loads(raw, option=option | yr.OPT_ROUND_TRIP)
    assert isinstance(doc, yr.YAMLRocksDocument)  # guaranteed by OPT_ROUND_TRIP
    if isinstance(doc.node.value, dict | list):
        _add_descriptions(doc.node, model, opts=add_comments)
        stream.write(doc.to_yaml().decode("utf-8"))
    else:
        warnings.warn(
            "Failed to add comments to model; is not a map or sequence.",
            category=UserWarning,
        )
        yr.dump(val, stream, option=option)
