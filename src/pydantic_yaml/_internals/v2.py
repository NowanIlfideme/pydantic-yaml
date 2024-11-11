"""Model for dumping Pydantic models.

See Also
--------
Roundtrip comments with ruamel.yaml
    https://yaml.readthedocs.io/en/latest/detail.html#round-trip-including-comments
    Currently, it's not possible to round-trip comments in `pydantic-yaml`.
    If you need to keep comments, you'll have to have parallel updating and validation.
"""

from io import IOBase
from pathlib import Path
from typing import TypeVar


from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


def to_yaml_str(model: BaseModel) -> str:
    """Generate a YAML string representation of the model.

    Parameters
    ----------
    model : BaseModel
        The model to convert.
    """
    raise NotImplementedError("TODO.")


def to_yaml_file(
    file: Path | str | IOBase,
    model: BaseModel,
) -> None:
    """Write a YAML file representation of the model.

    Parameters
    ----------
    file : Path or str or IOBase
        The file path or stream to write to.
    model : BaseModel
        The model to write.
    """
    raise NotImplementedError("TODO.")


def parse_yaml_raw_as(model_type: type[T], raw: str | bytes | IOBase) -> T:
    """Parse raw YAML string as the passed model type.

    Parameters
    ----------
    model_type : Type[BaseModel]
        The resulting model type.
    raw : str or bytes or IOBase
        The YAML string or stream.
    """
    raise NotImplementedError("TODO.")


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
