"""Model for dumping Pydantic models.

See Also
--------
Roundtrip comments with ruamel.yaml
    https://yaml.readthedocs.io/en/latest/detail.html#round-trip-including-comments
    Currently, it's not possible to round-trip comments in `pydantic-yaml`.
    If you need to keep comments, you'll have to have parallel updating and validation.
"""

import json
from io import StringIO, IOBase
from pathlib import Path
from typing import Any, Optional, Union

import pydantic
from ruamel.yaml import YAML
from pydantic import BaseModel


def _chk_model(model: Any) -> BaseModel:
    """Ensure the model passed is a Pydantic model."""
    if isinstance(model, BaseModel):
        return model
    raise TypeError("We can currently only write `pydantic.BaseModel`, " f"but recieved: {model!r}")


def _write_yaml_model(
    stream: IOBase,
    model: BaseModel,
    *,
    default_flow_style: Optional[bool] = None,
    indent: Optional[int] = None,
    map_indent: Optional[int] = None,
    sequence_indent: Optional[int] = None,
    sequence_dash_offset: Optional[int] = None,
    custom_yaml_writer: Optional[YAML] = None,
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
    model = _chk_model(model)
    if pydantic.version.VERSION < "2":
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
    model: BaseModel,
    *,
    default_flow_style: Optional[bool] = False,
    indent: Optional[int] = None,
    map_indent: Optional[int] = None,
    sequence_indent: Optional[int] = None,
    sequence_dash_offset: Optional[int] = None,
    custom_yaml_writer: Optional[YAML] = None,
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
    model = _chk_model(model)
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
    file: Union[Path, str, IOBase],
    model: BaseModel,
    *,
    default_flow_style: Optional[bool] = False,
    indent: Optional[int] = None,
    map_indent: Optional[int] = None,
    sequence_indent: Optional[int] = None,
    sequence_dash_offset: Optional[int] = None,
    custom_yaml_writer: Optional[YAML] = None,
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
    model = _chk_model(model)
    if isinstance(file, IOBase):
        _write_yaml_model(
            file,
            model,
            default_flow_style=default_flow_style,
            indent=indent,
            map_indent=map_indent,
            sequence_indent=sequence_indent,
            sequence_dash_offset=sequence_dash_offset,
            custom_yaml_writer=custom_yaml_writer,
            **json_kwargs,
        )
        return

    if isinstance(file, str):
        file = Path(file).resolve()
    elif isinstance(file, Path):
        file = file.resolve()
    else:
        raise TypeError(f"Expected Path, str, or stream, but got {file!r}")

    with file.open(mode="w") as f:
        _write_yaml_model(f, model, **json_kwargs)
