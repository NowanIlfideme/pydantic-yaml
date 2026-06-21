"""Module for dumping Pydantic models."""

__all__ = ["to_yaml_file", "to_yaml_str"]

import warnings

from pydantic_yaml._internals.v2 import to_yaml_file, to_yaml_str

warnings.warn(DeprecationWarning("This module is deprecated; use `from pydantic_yaml` instead."))
