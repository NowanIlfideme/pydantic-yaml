"""Model for dumping Pydantic models.

See Also
--------
Roundtrip comments with ruamel.yaml
    https://yaml.readthedocs.io/en/latest/detail.html#round-trip-including-comments
    Currently, it's not possible to round-trip comments in `pydantic-yaml`.
    If you need to keep comments, you'll have to have parallel updating and validation.
"""

import json
import os
import warnings
from collections.abc import Mapping, Sequence
from io import BytesIO, IOBase, StringIO
from pathlib import Path
from textwrap import dedent
from typing import Any, Literal, TypeVar

from pydantic import BaseModel, RootModel, TypeAdapter
from pydantic.fields import FieldInfo
from ruamel.yaml import YAML, CommentedMap, CommentedSeq

from pydantic_yaml._internals.comments import CommentsOptions, get_doc as _get_doc

EngineName = Literal["ruamel", "yamlrocks"]
"""Which YAML library is used to read/write.

`"ruamel"` (the `ruamel.yaml` package) is the default for now. `"yamlrocks"` is an
optional, Rust-backed engine (see `pydantic_yaml._internals.engine_yamlrocks` and
`issue #338 <https://github.com/NowanIlfideme/pydantic-yaml/issues/338>`_) that requires
installing `pydantic-yaml[yamlrocks]`.
"""

_ENGINES: tuple[EngineName, ...] = ("ruamel", "yamlrocks")
_ENGINE_ENV_VAR = "PYDANTIC_YAML_ENGINE"


def _validate_engine(engine: str) -> EngineName:
    if engine == "ruamel":
        return "ruamel"
    if engine == "yamlrocks":
        return "yamlrocks"
    raise ValueError(f"Unknown YAML engine {engine!r}; expected one of {_ENGINES!r}.")


def _engine_from_env() -> EngineName:
    raw = os.environ.get(_ENGINE_ENV_VAR)
    if raw is None:
        return "ruamel"
    return _validate_engine(raw)


_default_engine: EngineName = _engine_from_env()


def get_default_engine() -> EngineName:
    """Get the default YAML engine used when `engine=None` is passed to the public functions.

    Defaults to `"ruamel"`, or the value of the `PYDANTIC_YAML_ENGINE` environment variable
    (read once, at import time) if set.
    """
    return _default_engine


def set_default_engine(engine: EngineName) -> None:
    """Set the default YAML engine used when `engine=None` is passed to the public functions.

    Parameters
    ----------
    engine : "ruamel" or "yamlrocks"
        The engine to use by default from now on. `"yamlrocks"` requires the optional
        `yamlrocks` dependency; install it with `pip install pydantic-yaml[yamlrocks]`.
    """
    global _default_engine
    _default_engine = _validate_engine(engine)


def _resolve_engine(engine: EngineName | None) -> EngineName:
    if engine is None:
        return _default_engine
    return _validate_engine(engine)


def as_yaml_comment(value: str | None) -> str | None:
    """Convert a value (e.g. docstring) into a YAML comment."""
    if value is None:
        return None
    lines = dedent(value.lstrip("\n").rstrip()).split("\n")
    return "\n".join([f"# {v}".strip() for v in lines])


T = TypeVar("T", bound=BaseModel)


def _add_descriptions(
    ystruct: CommentedMap | CommentedSeq,  # or other stuff...
    obj: BaseModel | Mapping | Sequence | Any,
    opts: CommentsOptions,
) -> None:
    """Add descriptions from the object to the yaml struct (modifying it).

    This will fail if `ystruct` and `obj` don't have the same structure.
    """
    # Add top-level comment
    top_lvl = _get_doc(obj, opts=opts)
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
                fld_desc = _get_doc(fld_info, opts=opts)
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


def _write_yaml_model(
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
    engine: EngineName | None = None,
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
        More specific indent values. Only supported by the `"ruamel"` engine.
    custom_yaml_writer : None or YAML
        An instance of ruamel.yaml.YAML (or a subclass) to use as the writer.
        The above options will be set on it, if given. Only supported by the `"ruamel"` engine.
    engine : "ruamel" or "yamlrocks" or None
        Which YAML library to use. Defaults to `get_default_engine()`.
    json_kwargs : Any
        Keyword arguments to pass `model.model_dump_json()`.
    """
    if not isinstance(model, BaseModel):
        raise TypeError(f"Expected a Pydantic BaseModel, but got {type(model)}")

    resolved_engine = _resolve_engine(engine)
    if resolved_engine == "yamlrocks":
        if custom_yaml_writer is not None:
            raise TypeError(
                "`custom_yaml_writer` is specific to the 'ruamel' engine and cannot be "
                "combined with engine='yamlrocks'."
            )
        from pydantic_yaml._internals import engine_yamlrocks

        engine_yamlrocks.write_yaml_model(
            stream,
            model,
            add_comments=add_comments,
            default_flow_style=default_flow_style,
            indent=indent,
            map_indent=map_indent,
            sequence_indent=sequence_indent,
            sequence_dash_offset=sequence_dash_offset,
            **json_kwargs,
        )
        return

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


def to_yaml_str(
    model: BaseModel,
    *,
    add_comments: CommentsOptions = False,
    default_flow_style: bool | None = False,
    indent: int | None = None,
    map_indent: int | None = None,
    sequence_indent: int | None = None,
    sequence_dash_offset: int | None = None,
    custom_yaml_writer: YAML | None = None,
    engine: EngineName | None = None,
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
        More specific indent values. Only supported by the `"ruamel"` engine.
    custom_yaml_writer : None or YAML
        An instance of ruamel.yaml.YAML (or a subclass) to use as the writer.
        The above options will be set on it, if given. Only supported by the `"ruamel"` engine.
    engine : "ruamel" or "yamlrocks" or None
        Which YAML library to use. Defaults to `get_default_engine()` (currently `"ruamel"`
        unless changed via `set_default_engine()` or the `PYDANTIC_YAML_ENGINE` env var).
        `"yamlrocks"` requires the optional `pydantic-yaml[yamlrocks]` dependency.
    json_kwargs : Any
        Keyword arguments to pass `model.model_dump_json()`.

    Notes
    -----
    This currently uses JSON dumping as an intermediary.
    This means that you can use `json_encoders` in your model.
    """
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
        engine=engine,
        **json_kwargs,
    )
    stream.seek(0)
    return stream.read()


def to_yaml_file(
    file: Path | str | IOBase,
    model: BaseModel,
    *,
    add_comments: CommentsOptions = False,
    default_flow_style: bool | None = False,
    indent: int | None = None,
    map_indent: int | None = None,
    sequence_indent: int | None = None,
    sequence_dash_offset: int | None = None,
    custom_yaml_writer: YAML | None = None,
    engine: EngineName | None = None,
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
        More specific indent values. Only supported by the `"ruamel"` engine.
    custom_yaml_writer : None or YAML
        An instance of ruamel.yaml.YAML (or a subclass) to use as the writer.
        The above options will be set on it, if given. Only supported by the `"ruamel"` engine.
    engine : "ruamel" or "yamlrocks" or None
        Which YAML library to use. Defaults to `get_default_engine()` (currently `"ruamel"`
        unless changed via `set_default_engine()` or the `PYDANTIC_YAML_ENGINE` env var).
        `"yamlrocks"` requires the optional `pydantic-yaml[yamlrocks]` dependency.
    json_kwargs : Any
        Keyword arguments to pass `model.model_dump_json()`.

    Notes
    -----
    This currently uses JSON dumping as an intermediary.
    This means that you can use `json_encoders` in your model.
    """
    write_kwargs = dict(
        add_comments=add_comments,
        default_flow_style=default_flow_style,
        indent=indent,
        map_indent=map_indent,
        sequence_indent=sequence_indent,
        sequence_dash_offset=sequence_dash_offset,
        custom_yaml_writer=custom_yaml_writer,
        engine=engine,
        **json_kwargs,
    )
    if isinstance(file, IOBase):  # open file handle
        _write_yaml_model(file, model, **write_kwargs)  # type: ignore
        return

    if isinstance(file, str):  # local path to file
        file = Path(file).resolve()
    elif isinstance(file, Path):
        file = file.resolve()
    else:
        raise TypeError(f"Expected Path, str, or stream, but got {file!r}")

    with file.open(mode="w") as f:
        _write_yaml_model(f, model, **write_kwargs)  # type: ignore
        return


def parse_yaml_raw_as(
    model_type: type[T],
    raw: str | bytes | IOBase,
    *,
    engine: EngineName | None = None,
) -> T:
    """Parse raw YAML string as the passed model type.

    Parameters
    ----------
    model_type : Type[BaseModel]
        The resulting model type.
    raw : str or bytes or IOBase
        The YAML string or stream.
    engine : "ruamel" or "yamlrocks" or None
        Which YAML library to use. Defaults to `get_default_engine()` (currently `"ruamel"`
        unless changed via `set_default_engine()` or the `PYDANTIC_YAML_ENGINE` env var).
        `"yamlrocks"` requires the optional `pydantic-yaml[yamlrocks]` dependency.
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

    resolved_engine = _resolve_engine(engine)
    if resolved_engine == "yamlrocks":
        from pydantic_yaml._internals import engine_yamlrocks

        objects = engine_yamlrocks.read_yaml_stream(stream)
    else:
        reader = YAML(typ="safe", pure=True)  # YAML 1.2 support
        objects = reader.load(stream)
    ta = TypeAdapter(model_type)
    return ta.validate_python(objects)


def parse_yaml_file_as(
    model_type: type[T],
    file: Path | str | IOBase,
    *,
    engine: EngineName | None = None,
) -> T:
    """Parse YAML file as the passed model type.

    Parameters
    ----------
    model_type : Type[BaseModel]
        The resulting model type.
    file : Path or str or IOBase
        The file path or stream to read from.
    engine : "ruamel" or "yamlrocks" or None
        Which YAML library to use. Defaults to `get_default_engine()` (currently `"ruamel"`
        unless changed via `set_default_engine()` or the `PYDANTIC_YAML_ENGINE` env var).
        `"yamlrocks"` requires the optional `pydantic-yaml[yamlrocks]` dependency.
    """
    # Short-circuit
    if isinstance(file, IOBase):
        return parse_yaml_raw_as(model_type, raw=file, engine=engine)

    if isinstance(file, str):
        file = Path(file).resolve()
    elif isinstance(file, Path):
        file = file.resolve()
    else:
        raise TypeError(f"Expected Path, str or IO, but got {file!r}")

    with file.open(mode="r") as f:
        return parse_yaml_raw_as(model_type, f, engine=engine)
