"""Module for loading Pydantic models."""

from io import StringIO, BytesIO, IOBase
from pathlib import Path
from typing import Tuple, Type, Union, TypeVar

import pydantic
from ruamel.yaml import YAML


BaseModel: Type
BaseModelTuple: Tuple[Type, ...]

if pydantic.version.VERSION < "2":
    from pydantic import BaseModel as BaseModelV1

    BaseModel = BaseModelV1
    BaseModelTuple = (BaseModelV1,)
else:
    from pydantic import BaseModel as BaseModelV2
    from pydantic.v1 import BaseModel as BaseModelV1

    BaseModel = Union[BaseModelV1, BaseModelV2]
    BaseModelTuple = (BaseModelV1, BaseModelV2)


T = TypeVar("T", bound=BaseModel)


def parse_yaml_raw_as(model_type: Type[T], raw: Union[str, bytes, IOBase]) -> T:
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
