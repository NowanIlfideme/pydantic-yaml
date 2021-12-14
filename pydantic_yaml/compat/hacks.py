"""Module for some hacks that are needed to work around the YAML library interfaces.

Mainy, this defines "safe" representers for common types that Pydantic is able to parse.
"""

__all__ = ["inject_all"]

from typing import List, Type

from .representers import register_str_like, register_int_like


def get_str_like_types() -> List[Type]:
    """Returns many string-like types from stdlib and Pydantic."""

    # flake8: noqa

    from uuid import UUID
    from pathlib import (
        Path,
        PosixPath,
        PurePath,
        PurePosixPath,
        PureWindowsPath,
        WindowsPath,
    )

    from pydantic import types, networks

    def _chk(x) -> bool:
        try:
            return issubclass(x, (str, Path, PurePath, UUID))
        except Exception:
            return False

    # Get most candidates
    candidates = (
        list(locals().values())
        + [getattr(types, v) for v in types.__all__]
        + [getattr(networks, v) for v in networks.__all__]
    )
    str_like = [v for v in candidates if _chk(v)]

    # SecretStr, SecretBytes are stringified as "**********" by Pydantic
    str_like += [types.SecretStr, types.SecretBytes]
    return str_like


def get_int_like_types() -> List[Type]:
    """Returns many int-like types from stdlib and Pydantic."""

    from pydantic import types

    def _chk(x) -> bool:
        try:
            return issubclass(x, (int))
        except Exception:
            return False

    candidates = list(locals().values()) + [getattr(types, v) for v in types.__all__]
    int_like = [v for v in candidates if _chk(v)]
    return int_like


def inject_all():
    """Injects all necessary "hacks" into the namespace.
    
    What this currently does:
    - Registers many str-like and int-like types (from Pydantic and the standard
      library) to be representable in YAML.
    """
    # Add representers for string-like and int-like values.
    for cls in get_str_like_types():
        register_str_like(cls, method=str)
    for cls in get_int_like_types():
        register_int_like(cls)
