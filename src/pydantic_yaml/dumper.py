"""Module for dumping Pydantic models."""

__all__ = ["to_yaml_file", "to_yaml_str"]

import warnings
from pydantic.version import VERSION as PYDANTIC_VERSION

if (PYDANTIC_VERSION > "1") and (PYDANTIC_VERSION < "2"):
    from pydantic_yaml._internals.v1 import to_yaml_file, to_yaml_str
elif (PYDANTIC_VERSION > "2") and (PYDANTIC_VERSION < "3"):
    from pydantic_yaml._internals.v2 import to_yaml_file, to_yaml_str
else:
    raise ImportError(f"Unsupported version of Pydantic: {PYDANTIC_VERSION!r}")

warnings.warn(DeprecationWarning("This module is deprecated; use `from pydantic_yaml` instead."))
