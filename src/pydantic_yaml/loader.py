"""Module for loading Pydantic models."""

from io import StringIO, BytesIO, IOBase
from pathlib import Path
from typing import Type, Union, TypeVar

from pydantic import BaseModel, parse_obj_as
from ruamel.yaml import YAML

T = TypeVar("T", bound=BaseModel)


def parse_yaml_raw_as(model_type: Type[T], raw: Union[str, bytes, IOBase]) -> T:
    """Parse raw YAML string as the passed model type."""
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
    res = parse_obj_as(model_type, objects)
    return res


def parse_yaml_file_as(model_type: Type[T], file: Union[Path, str, IOBase]) -> T:
    """Parse YAML file as the passed model type."""
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
