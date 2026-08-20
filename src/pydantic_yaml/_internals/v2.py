"""Engine-agnostic YAML <-> Pydantic model plumbing.

The actual reading/writing is delegated entirely to a `pydantic_yaml.engines.YamlEngine` object
(the built-in `RuamelEngine`/`YamlRocksEngine`, or a custom one) - see
`pydantic_yaml.engines` for the engine interface, built-in implementations, and default-engine
resolution (`get_default_engine`/`set_default_engine`).
"""

from __future__ import annotations

from io import BytesIO, IOBase, StringIO
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel, TypeAdapter

from pydantic_yaml.engines import YamlEngine, get_default_engine

T = TypeVar("T", bound=BaseModel)


def to_yaml_str(model: BaseModel, *, engine: YamlEngine | None = None) -> str:
    """Generate a YAML string representation of the model.

    Parameters
    ----------
    model : BaseModel
        The model to convert.
    engine : YamlEngine or None
        The YAML engine to use (e.g. `RuamelEngine(...)`, `YamlRocksEngine(...)`, or a custom
        one). Defaults to `get_default_engine()` - whichever built-in is installed (preferring
        `YamlRocksEngine`), with default configuration.
    """
    resolved = engine if engine is not None else get_default_engine()
    stream = StringIO()
    resolved.write(stream, model)
    stream.seek(0)
    return stream.read()


def to_yaml_file(
    file: Path | str | IOBase, model: BaseModel, *, engine: YamlEngine | None = None
) -> None:
    """Write a YAML file representation of the model.

    Parameters
    ----------
    file : Path or str or IOBase
        The file path or stream to write to.
    model : BaseModel
        The model to write.
    engine : YamlEngine or None
        The YAML engine to use. Defaults to `get_default_engine()`.
    """
    resolved = engine if engine is not None else get_default_engine()

    if isinstance(file, IOBase):  # open file handle
        resolved.write(file, model)
        return

    if isinstance(file, str):  # local path to file
        file = Path(file).resolve()
    elif isinstance(file, Path):
        file = file.resolve()
    else:
        raise TypeError(f"Expected Path, str, or stream, but got {file!r}")

    with file.open(mode="w") as f:
        resolved.write(f, model)  # type: ignore[arg-type]
        return


def parse_yaml_raw_as(
    model_type: type[T],
    raw: str | bytes | IOBase,
    *,
    engine: YamlEngine | None = None,
) -> T:
    """Parse raw YAML string as the passed model type.

    Parameters
    ----------
    model_type : Type[BaseModel]
        The resulting model type.
    raw : str or bytes or IOBase
        The YAML string or stream.
    engine : YamlEngine or None
        The YAML engine to use. Defaults to `get_default_engine()`.
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

    resolved = engine if engine is not None else get_default_engine()
    objects = resolved.read(stream)
    ta = TypeAdapter(model_type)
    return ta.validate_python(objects)


def parse_yaml_file_as(
    model_type: type[T],
    file: Path | str | IOBase,
    *,
    engine: YamlEngine | None = None,
) -> T:
    """Parse YAML file as the passed model type.

    Parameters
    ----------
    model_type : Type[BaseModel]
        The resulting model type.
    file : Path or str or IOBase
        The file path or stream to read from.
    engine : YamlEngine or None
        The YAML engine to use. Defaults to `get_default_engine()`.
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
