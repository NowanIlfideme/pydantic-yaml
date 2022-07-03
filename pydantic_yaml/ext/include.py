"""Allows including external references."""


from abc import abstractmethod
from inspect import isabstract
from pathlib import Path
from typing import Any, Dict, Optional, Type, TypeVar

from pydantic import BaseModel, parse_file_as, root_validator

from pydantic_yaml.compat.types import YamlStr
from pydantic_yaml.model import YamlModel


K = TypeVar("K")
INCLUDE_STR = "include "


class BaseInclude(YamlStr):
    """Special type to allow including an external reference."""

    def __init_subclass__(cls, prefix: Optional[str] = None):
        if isabstract(cls):
            return
        if prefix is None:
            return

    @abstractmethod
    def load_reference(self, type_: Type[K]) -> K:
        """Loads the referenced include."""

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not isinstance(v, str):
            raise TypeError("Expected a string.")
        assert v.startswith(INCLUDE_STR)
        uri = v[len(INCLUDE_STR) :]
        # TODO: parse prefix?
        return cls(uri)


class FileInclude(YamlStr):
    """Include a file instead of a sub-model."""

    def load_reference(self, type_: Type[K]) -> K:
        """Parses the external reference, similar to `parse_file_as`."""
        path = Path(self)
        if not path.is_absolute():
            raise ValueError("Non-absolute paths are ambiguous and unsupported.")
        # FIXME: `parse_file_as` doesn't support YAML!
        return parse_file_as(type_, path)


class AllowReferences(BaseModel):
    """Mixin class that allows external references."""

    @root_validator()
    def _load_references(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Loads external references."""
        assert issubclass(cls, YamlModel)
        values = values.copy()
        updates = {}
        for k, v in values.items():
            if isinstance(v, BaseInclude):
                fld = cls.__fields__[k]
                updates[k] = v.load_reference(fld)
        values.update(updates)
        return values

