"""Model for dumping Pydantic models.

See Also
--------
Roundtrip comments with ruamel.yaml
    https://yaml.readthedocs.io/en/latest/detail.html#round-trip-including-comments
"""

import json
from io import StringIO, IOBase
from pathlib import Path
from typing import Union

from ruamel.yaml import YAML
from pydantic import BaseModel


def _write_yaml_model(stream: IOBase, model: BaseModel, **kwargs):
    """Write YAML model to the stream object.

    This uses JSON dumping as an intermediary.

    Parameters
    ----------
    stream : IOBase
        The stream to write to.
    model : BaseModel
        The model to convert.
    kwargs : Any
        Keyword arguments to pass `model.json()`. FIXME: Add explicit arguments.
    """
    json_val = model.json(**kwargs)
    val = json.loads(json_val)
    writer = YAML()
    # TODO: Configure writer
    # writer.default_flow_style = True or False or smth like that
    # writer.indent(...) for example
    writer.dump(val, stream)


def to_yaml_str(model: BaseModel, **kwargs) -> str:
    """Generate a YAML string representation of the model.

    Parameters
    ----------
    model : BaseModel
        The model to convert.
    kwargs : Any
        Keyword arguments to pass `model.json()`. FIXME: Add explicit arguments.

    Notes
    -----
    This currently uses JSON dumping as an intermediary.
    This means that you can use `json_encoders` in your model.
    """
    stream = StringIO()
    _write_yaml_model(stream, model, **kwargs)
    stream.seek(0)
    return stream.read()


def to_yaml_file(file: Union[Path, str, IOBase], model: BaseModel, **kwargs) -> None:
    """Write a YAML file representation of the model.

    Parameters
    ----------
    file : Path or str or IOBase
        The file path or stream to write to.
    model : BaseModel
        The model to convert.
    kwargs : Any
        Keyword arguments to pass `model.json()`. FIXME: Add explicit arguments.

    Notes
    -----
    This currently uses JSON dumping as an intermediary.
    This means that you can use `json_encoders` in your model.
    """
    if isinstance(file, IOBase):
        _write_yaml_model(file, model, **kwargs)

    if isinstance(file, str):
        file = Path(file).resolve()
    elif isinstance(file, Path):
        file = file.resolve()
    else:
        raise TypeError(f"Expected Path, str, or stream, but got {file!r}")

    with file.open(mode="w") as f:
        _write_yaml_model(f, model, **kwargs)
