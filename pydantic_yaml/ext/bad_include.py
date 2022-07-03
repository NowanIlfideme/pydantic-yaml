"""Adds ability to include external references in your YAML files.

This feature is NOT SECURE in the sense of potentially causing side effects. 
"""

from abc import ABC, abstractmethod
from inspect import isabstract
from pathlib import Path
from typing import Any, Optional, Tuple, Type, TypeVar, Union

from pydantic import parse_file_as

from pydantic_yaml.compat.yaml_lib import (
    dumper_classes,
    loader_classes,
    representer_classes,
    yaml,
)

__all__ = ["ExternalRef", "FileRef"]

K = TypeVar("K")


class ExternalRef(ABC):
    """Base data type for external references."""

    __slots__ = ("uri",)
    parsing_type: Optional[Type] = None

    def __init__(self, uri: str):
        self.uri = str(uri)

    def __init_subclass__(cls) -> None:
        """Registers concrete subclasses as something loadable from YAML."""
        if isabstract(cls):
            return
        tag = cls.__yaml_tag()
        for loader in loader_classes:
            loader.add_constructor(tag, cls.__constructor)
        for rd in dumper_classes + representer_classes:  # type: ignore
            rd.add_representer(cls, cls.__dumper)

    def __repr__(self) -> str:
        cn = type(self).__qualname__
        return f"{cn}({self.uri!r})"

    def __str__(self) -> str:
        return str(self.uri)

    def __class_getitem__(cls, type_: Union[Type, Tuple[Type]]) -> Type["ExternalRef"]:
        if isinstance(type_, tuple):
            type_ = Union[type_]  # type: ignore
        new_name = f"{cls.__qualname__}[{type_}]"

        class Subcls(cls):
            __qualname__ = new_name
            __name__ = new_name
            __module__ = cls.__module__
            parsing_type = type_

        return Subcls

    @classmethod
    def __yaml_tag(cls) -> str:
        """YAML tag for representation."""
        cn = type(cls).__qualname__
        tag = f"!{cn}"
        return tag

    @classmethod
    def __constructor(cls, loader: yaml.BaseLoader, node) -> "ExternalRef":
        return cls(loader.construct_scalar(node))

    @classmethod
    def __dumper(cls, dumper: yaml.BaseDumper, obj: "ExternalRef"):
        tag = cls.__yaml_tag()
        return dumper.represent_scalar(tag, obj.uri)

    @abstractmethod
    def parse_as(self, type_: Type[K]) -> K:
        """Parses the object given by this reference as the given `type_`."""

    def parse(self):
        """Parses the object given by this reference as the saved type."""
        if self.parsing_type is None:
            raise TypeError(f"Parsing type not set for for {self!r}.")
        return self.parse_as(self.parsing_type)

    @classmethod
    def __get_validators__(cls):
        """Pydantic validator implementation detail.
        
        See Also
        --------
        https://pydantic-docs.helpmanual.io/usage/types/#classes-with-__get_validators__
        """
        yield cls.validate

    @classmethod
    def validate(cls, v: Union[str, Any]) -> "ExternalRef":
        """Validates """
        if not isinstance(v, str):
            raise TypeError(f"Expected a string URI, got {v!r}")
        return cls(v)


class FileRef(ExternalRef):
    """External file reference, to load as a sub-model.
    
    Note
    ----
    This only supports paths that are absolute, due to ambiguity in relative paths:
    a 'relative path' would be relative to the current working directory;
    however, from the user's point-of-view, this would probably in fact be relative
    to the YAML file being loaded, which is often not in the cwd!
    """

    def parse_as(self, type_: Type[K],) -> K:
        """Parses the external reference, similar to `parse_file_as`."""
        path = Path(self.uri)
        if not path.is_absolute():
            raise ValueError("Non-absolute paths are ambiguous and unsupported.")
        # FIXME: `parse_file_as` doesn't support YAML!
        return parse_file_as(type_, path)
