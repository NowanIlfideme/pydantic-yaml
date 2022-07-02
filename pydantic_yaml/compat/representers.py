"""Representers for dumping common objects to YAML."""

from functools import partial
from typing import Any, Callable, TypeVar

from .yaml_lib import yaml, dumper_classes, representer_classes

CType = TypeVar("CType")

__all__ = ["register_str_like", "register_int_like"]


def dump_as_str(dumper: yaml.Dumper, data: Any, method: Callable[[Any], str] = str):
    """Represents an object as a string in YAML.

    Parameters
    ----------
    dumper : yaml.Dumper
        The dumper instance, such as `yaml.SafeDumper()`.
    data
        The object to dump. Ideally this is string-like.
    method : callable
        A method that converts `data` to a string. Default is `str`.

    Returns
    -------
    node
        The YAML internal node representation.
    """
    return dumper.represent_str(method(data))


def dump_as_int(dumper: yaml.Dumper, data: Any, method: Callable[[Any], int] = int):
    """Represents an object as an integer in YAML.

    Parameters
    ----------
    dumper : yaml.Dumper
        The dumper instance, such as `yaml.SafeDumper()`.
    data
        The object to dump. Ideally this is int-like.
    method : callable
        A method that converts `data` to an integer. Default is `int`.

    Returns
    -------
    node
        The YAML internal node representation.
    """
    return dumper.represent_int(method(data))


def register_str_like(cls: CType, method: Callable[[Any], str] = str) -> CType:
    """Registers `cls` to be dumped to YAML as a string.

    Parameters
    ----------
    cls : Type
        The class to represent.
    method : callable
        A method that converts objects of type `cls` to a string.
        Default is `str`.

    Returns
    -------
    cls
        This is the same as the input `cls`.
    """
    for x_cls in dumper_classes + representer_classes:  # type: ignore
        x_cls.add_representer(cls, partial(dump_as_str, method=method))
    return cls


def register_int_like(cls: CType, method: Callable[[Any], int] = int) -> CType:
    """Registers `cls` to be dumped to YAML as an integer.

    Parameters
    ----------
    cls : Type
        The class to represent.
    method : callable
        A method that converts objects of type `cls` to an integer.
        Default is `int`.

    Returns
    -------
    cls
        This is the same as the input `cls`.
    """
    for x_cls in dumper_classes + representer_classes:  # type: ignore
        x_cls.add_representer(cls, partial(dump_as_int, method=method))
    return cls
