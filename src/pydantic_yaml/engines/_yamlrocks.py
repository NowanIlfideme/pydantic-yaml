"""YAML engine backed by the `yamlrocks` library.

`yamlrocks` is a Rust-based YAML 1.2 implementation that passes the yaml-test-suite
(unlike `ruamel.yaml`, see
`issue #338 <https://github.com/NowanIlfideme/pydantic-yaml/issues/338>`_).
It is an *optional* dependency: install it with ``pip install pydantic-yaml[yamlrocks]``
(requires Python >=3.12).

Importing this module never requires `yamlrocks` to be installed - only constructing a
`YamlRocksEngine` (or calling `.read()`/`.write()` on one) does.
"""

from __future__ import annotations

import json
import warnings
from collections.abc import Mapping, Sequence
from io import IOBase
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, RootModel, model_validator

from pydantic_yaml._internals.comments import CommentsOptions, get_doc

__all__ = ["YamlRocksEngine"]


def _child_keys(node: Any) -> list[Any]:
    """Get the ordered keys/indices of a mapping/sequence node, or `[]` for anything else."""
    val = node.value
    if isinstance(val, dict):
        return list(val.keys())
    if isinstance(val, list):
        return list(range(len(val)))
    return []


def _add_descriptions(node: Any, obj: Any, opts: CommentsOptions) -> None:
    """Add descriptions from `obj` onto the round-tripped `node` tree (mutates in place).

    A "start comment" is emitted by setting `comment_before` on the *first child* of a mapping
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


class YamlRocksEngine(BaseModel):
    """YAML engine backed by `yamlrocks` (Rust-based, YAML 1.2 spec-compliant).

    Optional dependency: install with `pip install pydantic-yaml[yamlrocks]` (Python >=3.12).
    Instances are immutable (`frozen`); use `.model_copy(update={...})` to derive a variant.
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    add_comments: CommentsOptions = False
    """Whether to add comments to the output YAML using model docstrings and/or field
    descriptions."""

    default_flow_style: bool = False
    """Whether to use "flow style" (more compact). Block style by default."""

    sort_keys: bool = False
    """Whether to alphabetize mapping keys. `False` (the default) preserves declaration order."""

    indent: int | None = None
    """Indent width, applied uniformly to maps and sequences. Only `2`/`4`/`None` are
    representable - `yamlrocks` has no independently-configurable map/sequence indent or
    partial dash offset (unlike `RuamelEngine`); use that engine for finer-grained control."""

    option: int | None = None
    """Power-user escape hatch: raw `yamlrocks.OPT_*` bitflags, OR'd into the computed option
    int alongside the flags derived from the other fields above."""

    json_kwargs: dict[str, Any] = Field(default_factory=dict)
    """Extra keyword arguments forwarded to `model.model_dump_json(**json_kwargs)`."""

    @model_validator(mode="after")
    def _check_available(self) -> YamlRocksEngine:
        try:
            import yamlrocks  # noqa: F401
        except ImportError as e:
            raise ImportError(
                "The 'yamlrocks' engine requires the optional `yamlrocks` package. "
                "Install it with `pip install pydantic-yaml[yamlrocks]`."
            ) from e
        if self.indent not in (None, 2, 4):
            raise NotImplementedError(
                f"The 'yamlrocks' engine only supports `indent` values of 2 or 4, got {self.indent!r}; "
                "use `RuamelEngine` for finer-grained control."
            )
        return self

    def _resolve_option(self) -> int:
        import yamlrocks as yr

        if self.indent is None:
            # Mirrors ruamel.yaml's default (offset=0): sequence dashes aren't further indented.
            option = yr.OPT_INDENT_2 | yr.OPT_INDENTLESS_SEQUENCES
        elif self.indent == 2:
            option = yr.OPT_INDENT_2
        else:
            option = yr.OPT_INDENT_4
        if self.sort_keys:
            option |= yr.OPT_SORT_KEYS
        if self.default_flow_style:
            option |= yr.OPT_FLOW_STYLE
        if self.option is not None:
            option |= self.option
        return option

    def read(self, stream: IOBase) -> Any:
        """Read a YAML stream (str, bytes, or file-like object) into plain Python objects."""
        import yamlrocks as yr

        return yr.load(stream)

    def write(self, stream: IOBase, model: BaseModel) -> None:
        """Write `model` as YAML to `stream`, using this engine's own configuration."""
        import yamlrocks as yr

        if not isinstance(model, BaseModel):
            raise TypeError(f"Expected a Pydantic BaseModel, but got {type(model)}")
        json_val = model.model_dump_json(**self.json_kwargs)
        val = json.loads(json_val)

        option = self._resolve_option()

        if self.add_comments is False:
            yr.dump(val, stream, option=option)
            return
        if self.add_comments not in (True, "fields-only", "models-only"):
            raise ValueError(f"Invalid `add_comments` value: {self.add_comments!r}")

        # We need to roundtrip, same as the ruamel engine does.
        raw = yr.dumps(val, option=option)
        doc = yr.loads(raw, option=option | yr.OPT_ROUND_TRIP)
        assert isinstance(doc, yr.YAMLRocksDocument)  # guaranteed by OPT_ROUND_TRIP
        if isinstance(doc.node.value, dict | list):
            _add_descriptions(doc.node, model, opts=self.add_comments)
            stream.write(doc.to_yaml().decode("utf-8"))
        else:
            warnings.warn(
                "Failed to add comments to model; is not a map or sequence.",
                category=UserWarning,
            )
            yr.dump(val, stream, option=option)
