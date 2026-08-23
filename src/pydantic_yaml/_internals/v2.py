"""Reader/writer-agnostic YAML <-> Pydantic model plumbing.

Reading is delegated entirely to a `pydantic_yaml.engines.YamlReader` object, and writing to a
`pydantic_yaml.engines.YamlWriter` object (the built-in `RuamelReader`/`RuamelWriter` and
`YamlRocksReader`/`YamlRocksWriter`, or custom ones) - see `pydantic_yaml.engines` for the
interfaces, built-in implementations, and default resolution (`get_default_reader`/
`set_default_reader`/`get_default_writer`/`set_default_writer`).
"""

from __future__ import annotations

from io import BytesIO, IOBase, StringIO
from pathlib import Path
from typing import TypeVar

from pydantic import BaseModel, TypeAdapter

from pydantic_yaml.engines import YamlReader, YamlWriter, get_default_reader, get_default_writer

T = TypeVar("T", bound=BaseModel)


def to_yaml_str(model: BaseModel, *, writer: YamlWriter | None = None) -> str:
    """Generate a YAML string representation of the model.

    Parameters
    ----------
    model : BaseModel
        The model to convert.
    writer : YamlWriter or None
        The YAML writer to use (e.g. `RuamelWriter(...)`, `YamlRocksWriter(...)`, or a custom
        one). Defaults to `get_default_writer()` - whichever built-in is installed (preferring
        `YamlRocksWriter`), with default configuration.
    """
    resolved = writer if writer is not None else get_default_writer()
    stream = StringIO()
    resolved.write(stream, model)
    stream.seek(0)
    return stream.read()


def to_yaml_file(
    file: Path | str | IOBase, model: BaseModel, *, writer: YamlWriter | None = None
) -> None:
    """Write a YAML file representation of the model.

    Parameters
    ----------
    file : Path or str or IOBase
        The file path or stream to write to.
    model : BaseModel
        The model to write.
    writer : YamlWriter or None
        The YAML writer to use. Defaults to `get_default_writer()`.
    """
    resolved = writer if writer is not None else get_default_writer()

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
    reader: YamlReader | None = None,
) -> T:
    """Parse raw YAML string as the passed model type.

    Parameters
    ----------
    model_type : Type[BaseModel]
        The resulting model type.
    raw : str or bytes or IOBase
        The YAML string or stream.
    reader : YamlReader or None
        The YAML reader to use. Defaults to `get_default_reader()`.
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

    resolved = reader if reader is not None else get_default_reader()
    objects = resolved.read(stream)
    ta = TypeAdapter(model_type)
    return ta.validate_python(objects)


def parse_yaml_file_as(
    model_type: type[T],
    file: Path | str | IOBase,
    *,
    reader: YamlReader | None = None,
) -> T:
    """Parse YAML file as the passed model type.

    Parameters
    ----------
    model_type : Type[BaseModel]
        The resulting model type.
    file : Path or str or IOBase
        The file path or stream to read from.
    reader : YamlReader or None
        The YAML reader to use. Defaults to `get_default_reader()`.
    """
    # Short-circuit
    if isinstance(file, IOBase):
        return parse_yaml_raw_as(model_type, raw=file, reader=reader)

    if isinstance(file, str):
        file = Path(file).resolve()
    elif isinstance(file, Path):
        file = file.resolve()
    else:
        raise TypeError(f"Expected Path, str or IO, but got {file!r}")

    with file.open(mode="r") as f:
        return parse_yaml_raw_as(model_type, f, reader=reader)
