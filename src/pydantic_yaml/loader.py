"""Module for loading Pydantic models."""

__all__ = ["parse_yaml_raw_as", "parse_yaml_file_as"]

import warnings

from pydantic_yaml._internals.v2 import parse_yaml_file_as, parse_yaml_raw_as

warnings.warn(DeprecationWarning("This module is deprecated; use `from pydantic_yaml` instead."))
