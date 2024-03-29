"""Module for loading Pydantic models."""

__all__ = ["parse_yaml_raw_as", "parse_yaml_file_as"]

import warnings
from pydantic.version import VERSION as PYDANTIC_VERSION

if (PYDANTIC_VERSION > "1") and (PYDANTIC_VERSION < "2"):
    from pydantic_yaml._internals.v1 import parse_yaml_raw_as, parse_yaml_file_as
elif (PYDANTIC_VERSION > "2") and (PYDANTIC_VERSION < "3"):
    from pydantic_yaml._internals.v2 import parse_yaml_raw_as, parse_yaml_file_as
else:
    raise ImportError(f"Unsupported version of Pydantic: {PYDANTIC_VERSION!r}")

warnings.warn(DeprecationWarning("This module is deprecated; use `from pydantic_yaml` instead."))
