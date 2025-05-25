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
from io import BytesIO, IOBase, StringIO
from pathlib import Path
from typing import Any, TypeVar
from typing_extensions import Literal  # noqa

from pydantic.version import VERSION as PYDANTIC_VERSION
from ruamel.yaml import YAML

if (PYDANTIC_VERSION < "2") or (PYDANTIC_VERSION > "3"):
    raise ImportError("This module can only be imported in Pydantic v2.")

from pydantic import BaseModel, TypeAdapter
from pydantic.v1 import BaseModel as BaseModelV1
from pydantic.v1 import parse_obj_as

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


def _write_yaml_model(
    stream: IOBase,
    model: BaseModel | BaseModelV1,
    *,
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
        Keyword arguments to pass `model.json()`.
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
        raise TypeError(f"Please pass a YAML instance or subclass. Got {custom_yaml_writer!r}")
    # Set options
    if default_flow_style is not None:
        writer.default_flow_style = default_flow_style
    writer.indent(mapping=indent, sequence=indent, offset=indent)
    writer.indent(mapping=map_indent, sequence=sequence_indent, offset=sequence_dash_offset)
    # TODO: Configure writer further?
    writer.dump(val, stream)


def to_yaml_str(
    model: BaseModel | BaseModelV1,
    *,
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
        Keyword arguments to pass `model.json()`.

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
        Keyword arguments to pass `model.json()`.

    Notes
    -----
    This currently uses JSON dumping as an intermediary.
    This means that you can use `json_encoders` in your model.
    """
    model, _ = _chk_model(model)
    write_kwargs = dict(
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
