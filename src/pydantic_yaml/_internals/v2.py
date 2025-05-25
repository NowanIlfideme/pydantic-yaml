"""Model for dumping Pydantic models.

See Also
--------
Roundtrip comments with ruamel.yaml
    https://yaml.readthedocs.io/en/latest/detail.html#round-trip-including-comments
    Currently, it's not possible to round-trip comments in `pydantic-yaml`.
    If you need to keep comments, you'll have to have parallel updating and validation.
"""

# mypy: ignore-errors

import json
import warnings
from collections.abc import Mapping, Sequence
from io import BytesIO, IOBase, StringIO
from pathlib import Path
from typing import Any, TypeVar
from typing_extensions import Literal  # noqa

from pydantic.version import VERSION as PYDANTIC_VERSION
from ruamel.yaml import CommentedMap, CommentedSeq, YAML

if (PYDANTIC_VERSION < "2") or (PYDANTIC_VERSION > "3"):
    raise ImportError("This module can only be imported in Pydantic v2.")

from pydantic import BaseModel, RootModel, TypeAdapter
from pydantic.v1 import BaseModel as BaseModelV1
from pydantic.v1 import parse_obj_as
from pydantic.v1.fields import FieldInfo as FieldInfoV1
from pydantic.fields import FieldInfo

from .comments import CommentsOptions

T = TypeVar("T", bound=BaseModel | BaseModelV1)


def _chk_model(model: Any) -> tuple[BaseModel | BaseModelV1, Literal[1, 2]]:
    """Ensure the model passed is a Pydantic model."""
    if isinstance(model, BaseModel):
        return model, 2
    elif isinstance(model, BaseModelV1):
        return model, 1
    raise TypeError(
        "We can currently only write `pydantic.BaseModel` or `pydantic.v1.BaseModel`"
        f"but recieved: {model!r}"
    )


def _get_doc(
    obj: BaseModel | BaseModelV1 | FieldInfo | FieldInfoV1 | Any, opts: CommentsOptions
) -> str | None:
    """Get documentation for the model or field, taking options into account."""
    if isinstance(obj, BaseModel | BaseModelV1):
        if opts in (True, "models-only"):
            return getattr(obj, "__doc__", None)
        return None
    elif isinstance(obj, FieldInfo | FieldInfoV1):
        if opts in (True, "fields-only"):
            return obj.description
        return None
    return None


def _add_descriptions(
    ystruct: CommentedMap | CommentedSeq,  # or other stuff...
    obj: BaseModel | BaseModelV1 | Mapping | Sequence | Any,
    opts: CommentsOptions,
) -> None:
    """Add descriptions from the object to the yaml struct (modifying it).

    This will fail if `ystruct` and `obj` don't have the same structure.
    """
    # Add top-level comment
    top_lvl = _get_doc(obj, opts=opts)
    if top_lvl is not None:
        try:
            indent = ystruct.lc.col  # type: ignore  # HACK
        except Exception:
            indent = 0
        ystruct.yaml_set_start_comment(top_lvl, indent=indent)

    if isinstance(obj, BaseModel):
        if obj.__pydantic_root_model__:
            # RootModel should probably work
            assert isinstance(obj, RootModel), "Model incorrectly set as RootModel."
            obj = obj.root
    elif isinstance(obj, BaseModelV1):
        if obj.__custom_root_type__:
            # RootModel should probably work
            obj = obj.__dict__["__root__"]

    if isinstance(obj, BaseModel | BaseModelV1):
        # Add field information
        flds: dict[str, FieldInfo] | dict[str, FieldInfoV1]

        if isinstance(obj, BaseModel):
            flds = obj.model_fields
        elif isinstance(obj, BaseModelV1):
            flds = obj.__fields__

        for fld_name, fld_info in flds.items():
            if fld_name in ystruct.keys():
                # Add field description (if any/allowed)
                fld_desc = _get_doc(fld_info, opts=opts)
                if fld_desc is not None:
                    ystruct.yaml_add_eol_comment(fld_desc, key=fld_name)

                # Recurse into fields
                fld_obj = getattr(obj, fld_name, None)
                if isinstance(fld_obj, BaseModel | BaseModelV1 | Sequence | Mapping):
                    _add_descriptions(ystruct[fld_name], fld_obj, opts=opts)
                # otherwise - no additional descriptions
    elif isinstance(obj, Sequence) and isinstance(ystruct, CommentedSeq):
        # Recurse into parts of the sequence; needed in cases of `list[dict[str, MyModel]]` and such
        for i, sub_obj in enumerate(obj):
            _add_descriptions(ystruct[i], sub_obj, opts=opts)
    elif isinstance(obj, Mapping) and isinstance(ystruct, CommentedMap):
        for key, sub_obj in obj.items():
            _add_descriptions(ystruct[key], sub_obj, opts=opts)


def _write_yaml_model(
    stream: IOBase,
    model: BaseModel | BaseModelV1,
    *,
    add_comments: CommentsOptions = False,
    default_flow_style: bool | None = None,
    indent: int | None = None,
    map_indent: int | None = None,
    sequence_indent: int | None = None,
    sequence_dash_offset: int | None = None,
    custom_yaml_writer: YAML | None = None,
    **json_kwargs,
) -> None:
    """Write YAML model to the stream object.

    This uses JSON dumping as an intermediary.

    Parameters
    ----------
    stream : IOBase
        The stream to write to.
    model : BaseModel
        The model to write.
    add_comments : False or True or "fields-only" or "models-only"
        Whether to add comments to the output YAML using fields and/or model descriptions.
    default_flow_style : bool
        Whether to use "flow style" (more human-readable).
        https://yaml.readthedocs.io/en/latest/detail.html?highlight=default_flow_style#indentation-of-block-sequences
    indent : None or int
        General indent value. Leave as None for the default.
    map_indent, sequence_indent, sequence_dash_offset : None or int
        More specific indent values.
    custom_yaml_writer : None or YAML
        An instance of ruamel.yaml.YAML (or a subclass) to use as the writer.
        The above options will be set on it, if given.
    json_kwargs : Any
        Keyword arguments to pass `model.model_dump_json()`.
    """
    model, vers = _chk_model(model)
    if vers == 1:
        json_val = model.json(**json_kwargs)  # type: ignore
    else:
        json_val = model.model_dump_json(**json_kwargs)  # type: ignore
    val = json.loads(json_val)
    # Allow setting custom writer
    if custom_yaml_writer is None:
        writer = YAML(typ="safe", pure=True)
    elif isinstance(custom_yaml_writer, YAML):
        writer = custom_yaml_writer
    else:
        raise TypeError(
            f"Please pass a YAML instance or subclass. Got {custom_yaml_writer!r}"
        )
    # Set options
    if default_flow_style is not None:
        writer.default_flow_style = default_flow_style
    writer.indent(mapping=indent, sequence=indent, offset=indent)
    writer.indent(
        mapping=map_indent, sequence=sequence_indent, offset=sequence_dash_offset
    )
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


def to_yaml_str(
    model: BaseModel | BaseModelV1,
    *,
    add_comments: CommentsOptions = False,
    default_flow_style: bool | None = False,
    indent: int | None = None,
    map_indent: int | None = None,
    sequence_indent: int | None = None,
    sequence_dash_offset: int | None = None,
    custom_yaml_writer: YAML | None = None,
    **json_kwargs,
) -> str:
    """Generate a YAML string representation of the model.

    Parameters
    ----------
    model : BaseModel
        The model to convert.
    add_comments : False or "all" or "fields-only" or "models-only"
        Whether to add comments to the output YAML using fields and/or model descriptions.
    default_flow_style : bool
        Whether to use "flow style" (more human-readable).
        https://yaml.readthedocs.io/en/latest/detail.html?highlight=default_flow_style#indentation-of-block-sequences
    indent : None or int
        General indent value. Leave as None for the default.
    map_indent, sequence_indent, sequence_dash_offset : None or int
        More specific indent values.
    custom_yaml_writer : None or YAML
        An instance of ruamel.yaml.YAML (or a subclass) to use as the writer.
        The above options will be set on it, if given.
    json_kwargs : Any
        Keyword arguments to pass `model.model_dump_json()`.

    Notes
    -----
    This currently uses JSON dumping as an intermediary.
    This means that you can use `json_encoders` in your model.
    """
    model, _ = _chk_model(model)
    stream = StringIO()
    _write_yaml_model(
        stream,
        model,
        add_comments=add_comments,
        default_flow_style=default_flow_style,
        indent=indent,
        map_indent=map_indent,
        sequence_indent=sequence_indent,
        sequence_dash_offset=sequence_dash_offset,
        custom_yaml_writer=custom_yaml_writer,
        **json_kwargs,
    )
    stream.seek(0)
    return stream.read()


def to_yaml_file(
    file: Path | str | IOBase,
    model: BaseModel | BaseModelV1,
    *,
    add_comments: CommentsOptions = False,
    default_flow_style: bool | None = False,
    indent: int | None = None,
    map_indent: int | None = None,
    sequence_indent: int | None = None,
    sequence_dash_offset: int | None = None,
    custom_yaml_writer: YAML | None = None,
    **json_kwargs,
) -> None:
    """Write a YAML file representation of the model.

    Parameters
    ----------
    file : Path or str or IOBase
        The file path or stream to write to.
    model : BaseModel
        The model to write.
    add_comments : False or "all" or "fields-only" or "models-only"
        Whether to add comments to the output YAML using fields and/or model descriptions.
    default_flow_style : bool
        Whether to use "flow style" (more human-readable).
        https://yaml.readthedocs.io/en/latest/detail.html?highlight=default_flow_style#indentation-of-block-sequences
    indent : None or int
        General indent value. Leave as None for the default.
    map_indent, sequence_indent, sequence_dash_offset : None or int
        More specific indent values.
    custom_yaml_writer : None or YAML
        An instance of ruamel.yaml.YAML (or a subclass) to use as the writer.
        The above options will be set on it, if given.
    json_kwargs : Any
        Keyword arguments to pass `model.model_dump_json()`.

    Notes
    -----
    This currently uses JSON dumping as an intermediary.
    This means that you can use `json_encoders` in your model.
    """
    model, _ = _chk_model(model)
    write_kwargs = dict(
        add_comments=add_comments,
        default_flow_style=default_flow_style,
        indent=indent,
        map_indent=map_indent,
        sequence_indent=sequence_indent,
        sequence_dash_offset=sequence_dash_offset,
        custom_yaml_writer=custom_yaml_writer,
        **json_kwargs,
    )
    if isinstance(file, IOBase):  # open file handle
        _write_yaml_model(file, model, **write_kwargs)
        return

    if isinstance(file, str):  # local path to file
        file = Path(file).resolve()
    elif isinstance(file, Path):
        file = file.resolve()
    else:
        raise TypeError(f"Expected Path, str, or stream, but got {file!r}")

    with file.open(mode="w") as f:
        _write_yaml_model(f, model, **write_kwargs)
        return


def parse_yaml_raw_as(model_type: type[T], raw: str | bytes | IOBase) -> T:
    """Parse raw YAML string as the passed model type.

    Parameters
    ----------
    model_type : Type[BaseModel]
        The resulting model type.
    raw : str or bytes or IOBase
        The YAML string or stream.
    """
    stream: IOBase
    if isinstance(raw, str):
        stream = StringIO(raw)
    elif isinstance(raw, bytes):
        stream = BytesIO(raw)
    elif isinstance(raw, IOBase):
        stream = raw
    else:
        raise TypeError(f"Expected str, bytes or IO, but got {raw!r}")
    reader = YAML(typ="safe", pure=True)  # YAML 1.2 support
    objects = reader.load(stream)
    if isinstance(model_type, type) and issubclass(model_type, BaseModelV1):
        return parse_obj_as(model_type, objects)  # type:ignore
    else:
        ta = TypeAdapter(model_type)  # type: ignore
        return ta.validate_python(objects)


def parse_yaml_file_as(model_type: type[T], file: Path | str | IOBase) -> T:
    """Parse YAML file as the passed model type.

    Parameters
    ----------
    model_type : Type[BaseModel]
        The resulting model type.
    file : Path or str or IOBase
        The file path or stream to read from.
    """
    # Short-circuit
    if isinstance(file, IOBase):
        return parse_yaml_raw_as(model_type, raw=file)

    if isinstance(file, str):
        file = Path(file).resolve()
    elif isinstance(file, Path):
        file = file.resolve()
    else:
        raise TypeError(f"Expected Path, str or IO, but got {file!r}")

    with file.open(mode="r") as f:
        return parse_yaml_raw_as(model_type, f)
