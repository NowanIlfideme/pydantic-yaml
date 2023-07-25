"""Module for loading Pydantic models."""

from io import StringIO, BytesIO, IOBase
from pathlib import Path
from typing import Type, Union, TypeVar

import pydantic
from pydantic import BaseModel
from ruamel.yaml import YAML

T = TypeVar("T", bound=BaseModel)


def parse_yaml_raw_section_as(
    section_name: str, model_type: Type[T], raw: Union[str, bytes, IOBase]
) -> T:
    """Parse raw YAML string as the passed model type.

    Parameters
    ----------
    section_name : str
        The name of the section in the YAML string
        to be parsed as model_type
    model_type : Type[BaseModel]
        The resulting model type.
    raw : str or bytes or IOBase
        The YAML string or stream.
    """
    stream = _get_stream_from_raw(raw)
    reader = YAML(typ="safe", pure=True)  # YAML 1.2 support
    objects = reader.load(stream)
    return _parse_dict_as(model_type, objects[section_name])

def parse_yaml_raw_as(model_type: Type[T], raw: Union[str, bytes, IOBase]) -> T:
    """Parse raw YAML string as the passed model type.

    Parameters
    ----------
    model_type : Type[BaseModel]
        The resulting model type.
    raw : str or bytes or IOBase
        The YAML string or stream.
    """
    stream = _get_stream_from_raw(raw)
    reader = YAML(typ="safe", pure=True)  # YAML 1.2 support
    objects = reader.load(stream)
    return _parse_dict_as(model_type, objects)


def _get_stream_from_raw(raw: Union[str, bytes, IOBase]) -> Union[StringIO, BytesIO, IOBase]:
    if isinstance(raw, str):
        return StringIO(raw)
    if isinstance(raw, bytes):
        return BytesIO(raw)
    if isinstance(raw, IOBase):
        return raw
    raise TypeError(f"Expected str, bytes or IO, but got {raw!r}")


def _parse_dict_as(model_type: Type[T], objects: dict) -> T:
    """Internal function to turn a dict representation of yaml file into
    a pydantic object"""

    if pydantic.version.VERSION < "2":
        return pydantic.parse_obj_as(model_type, objects)  # type:ignore
    else:
        ta = pydantic.TypeAdapter(model_type)  # type: ignore
        return ta.validate_python(objects)


def parse_yaml_file_as(model_type: Type[T], file: Union[Path, str, IOBase]) -> T:
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
