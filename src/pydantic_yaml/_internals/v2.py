"""Engine-agnostic YAML <-> Pydantic model plumbing.

The actual reading/writing is delegated to `pydantic_yaml._internals.engine_yamlrocks` or
`pydantic_yaml._internals.engine_ruamel`, imported lazily, since both YAML backends are
optional dependencies (see `issue #338 <https://github.com/NowanIlfideme/pydantic-yaml/issues/338>`_):
at least one of `pydantic-yaml[yamlrocks]` / `pydantic-yaml[ruamel]` must be installed, but
either one suffices.
"""

from __future__ import annotations

import importlib.util
import os
from io import BytesIO, IOBase, StringIO
from pathlib import Path
from typing import TYPE_CHECKING, Literal, TypeVar

from pydantic import BaseModel, TypeAdapter

from pydantic_yaml._internals.comments import CommentsOptions

if TYPE_CHECKING:
    from ruamel.yaml import YAML

EngineName = Literal["ruamel", "yamlrocks"]
"""Which YAML library is used to read/write.

`"yamlrocks"` (a Rust-backed engine, see `pydantic_yaml._internals.engine_yamlrocks`) and
`"ruamel"` (the `ruamel.yaml` package, the historical default) are both optional dependencies;
at least one must be installed. If neither `engine=` nor
`set_default_engine()`/`PYDANTIC_YAML_ENGINE` picks one explicitly, whichever is installed is
used automatically (preferring `"yamlrocks"` if both are present).
"""

_ENGINES: tuple[EngineName, ...] = ("yamlrocks", "ruamel")
_ENGINE_MODULES: dict[EngineName, str] = {"ruamel": "ruamel.yaml", "yamlrocks": "yamlrocks"}
_ENGINE_ENV_VAR = "PYDANTIC_YAML_ENGINE"


def _validate_engine(engine: str) -> EngineName:
    if engine == "ruamel":
        return "ruamel"
    if engine == "yamlrocks":
        return "yamlrocks"
    raise ValueError(f"Unknown YAML engine {engine!r}; expected one of {_ENGINES!r}.")


def _module_available(module_name: str) -> bool:
    try:
        return importlib.util.find_spec(module_name) is not None
    except ImportError:
        return False


def _autodetect_engine() -> EngineName:
    for name in _ENGINES:
        if _module_available(_ENGINE_MODULES[name]):
            return name
    raise ImportError(
        "pydantic-yaml requires at least one YAML backend to be installed. Install one with "
        "`pip install pydantic-yaml[yamlrocks]` or `pip install pydantic-yaml[ruamel]` "
        "(matches the historical default)."
    )


def _engine_from_env_or_autodetect() -> EngineName:
    raw = os.environ.get(_ENGINE_ENV_VAR)
    if raw is not None:
        return _validate_engine(raw)
    return _autodetect_engine()


# Resolved lazily (on first use) rather than at import time, so `import pydantic_yaml` never
# fails just because engine autodetection hasn't happened yet.
_default_engine: EngineName | None = None


def get_default_engine() -> EngineName:
    """Get the default YAML engine used when `engine=None` is passed to the public functions.

    Resolved once (and cached) on first use: the `PYDANTIC_YAML_ENGINE` environment variable if
    set, otherwise whichever of `"yamlrocks"`/`"ruamel"` is installed (preferring `"yamlrocks"`
    if both are present). Raises `ImportError` if neither is installed.
    """
    global _default_engine
    if _default_engine is None:
        _default_engine = _engine_from_env_or_autodetect()
    return _default_engine


def set_default_engine(engine: EngineName) -> None:
    """Set the default YAML engine used when `engine=None` is passed to the public functions.

    Parameters
    ----------
    engine : "ruamel" or "yamlrocks"
        The engine to use by default from now on. Must already be installed; install it with
        `pip install pydantic-yaml[yamlrocks]` or `pip install pydantic-yaml[ruamel]`.
    """
    global _default_engine
    validated = _validate_engine(engine)
    if not _module_available(_ENGINE_MODULES[validated]):
        raise ImportError(
            f"Cannot set the default engine to {validated!r}: the "
            f"`{_ENGINE_MODULES[validated]}` package isn't installed. "
            f"Install it with `pip install pydantic-yaml[{validated}]`."
        )
    _default_engine = validated


def _resolve_engine(engine: EngineName | None) -> EngineName:
    if engine is None:
        return get_default_engine()
    return _validate_engine(engine)


T = TypeVar("T", bound=BaseModel)


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

    from pydantic_yaml._internals import engine_ruamel

    engine_ruamel.write_yaml_model(
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
        Which YAML library to use. Defaults to `get_default_engine()`: whichever of
        `"yamlrocks"` / `"ruamel"` is installed (preferring `"yamlrocks"` if both are), unless
        overridden via `set_default_engine()` or the `PYDANTIC_YAML_ENGINE` env var. At least
        one of `pydantic-yaml[yamlrocks]` / `pydantic-yaml[ruamel]` must be installed.
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
        Which YAML library to use. Defaults to `get_default_engine()`: whichever of
        `"yamlrocks"` / `"ruamel"` is installed (preferring `"yamlrocks"` if both are), unless
        overridden via `set_default_engine()` or the `PYDANTIC_YAML_ENGINE` env var. At least
        one of `pydantic-yaml[yamlrocks]` / `pydantic-yaml[ruamel]` must be installed.
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
        Which YAML library to use. Defaults to `get_default_engine()`: whichever of
        `"yamlrocks"` / `"ruamel"` is installed (preferring `"yamlrocks"` if both are), unless
        overridden via `set_default_engine()` or the `PYDANTIC_YAML_ENGINE` env var. At least
        one of `pydantic-yaml[yamlrocks]` / `pydantic-yaml[ruamel]` must be installed.
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
        from pydantic_yaml._internals import engine_ruamel

        objects = engine_ruamel.read_yaml_stream(stream)
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
        Which YAML library to use. Defaults to `get_default_engine()`: whichever of
        `"yamlrocks"` / `"ruamel"` is installed (preferring `"yamlrocks"` if both are), unless
        overridden via `set_default_engine()` or the `PYDANTIC_YAML_ENGINE` env var. At least
        one of `pydantic-yaml[yamlrocks]` / `pydantic-yaml[ruamel]` must be installed.
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
