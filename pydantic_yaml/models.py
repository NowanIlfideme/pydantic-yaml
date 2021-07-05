from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Optional, Type, TypeVar, Union

from pydantic.main import BaseModel
from pydantic.error_wrappers import ErrorWrapper, ValidationError
from pydantic.types import StrBytes
from pydantic.parse import Protocol
from pydantic.utils import ROOT_KEY

from ._yaml import yaml

__all__ = ["YamlModel"]

try:
    from typing import Literal

    ExtendedProto = Union[Protocol, Literal["yaml"]]
except ImportError:
    # I think this would happen with Python < 3.8
    ExtendedProto = Union[Protocol, str]


def is_yaml_requested(content_type: str = None, proto: ExtendedProto = None):
    if content_type is None:
        is_yaml = False
    else:
        is_yaml = ("yaml" in content_type) or ("yml" in content_type)
    is_yaml = is_yaml or (proto == "yaml")
    return is_yaml


T = TypeVar('T', bound='YamlModel')


class YamlModel(BaseModel):
    """YAML-aware Pydantic model base class."""

    def yaml(
        self,
        *,
        include=None,
        exclude=None,
        by_alias: bool = False,
        skip_defaults: bool = None,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        encoder: Optional[Callable[[Any], Any]] = None,
        **dumps_kwargs: Any,
    ) -> str:
        """Generates a YAML representation of the model.

        Note that JSON is a subset of the YAMl spec, however this
        generates a multi-line, more-human-readable representation.
        """
        data = self.dict(
            include=include,
            exclude=exclude,
            by_alias=by_alias,
            skip_defaults=skip_defaults,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
        )
        res = yaml.safe_dump(data)
        return res

    @classmethod
    def parse_raw(
        cls: Type[T],
        b: StrBytes,
        *,
        content_type: str = None,
        encoding: str = None,
        proto: ExtendedProto = None,
        allow_pickle: bool = False,
    ) -> T:

        # Check whether we're specifically asked to parse YAML
        is_yaml = is_yaml_requested(content_type, proto)

        # Assume we're parsing YAML anyways
        # NOTE: JSON is a subset of the YAML spec
        try:
            obj = yaml.safe_load(b)
            res = cls.parse_obj(obj)
            return res
        except RecursionError as e:
            raise ValueError(
                "YAML files with recursive references are unsupported."
            ) from e
        except ValidationError:
            raise
        except Exception as e:
            if is_yaml:  # specifically requested YAML, so we error
                raise ValidationError([ErrorWrapper(e, loc=ROOT_KEY)], cls) from e

        # We had an error parsing as YAML, so let's try other formats :)
        return super().parse_raw(
            b,
            content_type=content_type,
            encoding=encoding,
            proto=proto,
            allow_pickle=allow_pickle,
        )

    @classmethod
    def parse_file(
        cls: Type[T],
        path: Union[str, Path],
        *,
        content_type: str = None,
        encoding: str = "utf-8",
        proto: ExtendedProto = None,
        allow_pickle: bool = False,
    ) -> T:

        # Check whether we're specifically asked to parse YAML
        is_yaml = is_yaml_requested(content_type, proto)

        # Assume we're parsing YAML anyways
        # NOTE: JSON is a subset of the YAML spec
        try:
            path = Path(path)
            b = path.read_bytes()
            return cls.parse_raw(
                b,
                content_type=content_type,
                encoding=encoding,
                proto="yaml",
                allow_pickle=allow_pickle,
            )
        except ValidationError:
            raise
        except Exception:
            if is_yaml:  # specifically requested YAML, so we error
                raise

        return super().parse_file(
            path,
            content_type=content_type,
            encoding=encoding,
            proto=proto,
            allow_pickle=allow_pickle,
        )
