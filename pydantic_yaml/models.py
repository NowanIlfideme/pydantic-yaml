from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional, Type, Any, Union

from pydantic.main import BaseModel
from pydantic.error_wrappers import ErrorWrapper, ValidationError
from pydantic.types import StrBytes
from pydantic.parse import Protocol
from pydantic.utils import ROOT_KEY

from pydantic_yaml._yaml import yaml

__all__ = ["YamlModel"]

try:
    from typing import Literal

    ExtendedProto = Union[Protocol, Literal["yaml"]]
except ImportError:
    # I think this would happen with Python < 3.8
    ExtendedProto = Union[Protocol, str]


class YamlModel(BaseModel):
    """YAML-aware Pydantic model base class."""

    def yaml(
        self,
        *,
        include,
        exclude,
        by_alias: bool,
        skip_defaults: bool,
        exclude_unset: bool,
        exclude_defaults: bool,
        exclude_none: bool,
        encoder: Optional[Callable[[Any], Any]],
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
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
        )
        res = yaml.dump(data)
        return res

    @classmethod
    def parse_raw(
        cls: Type[YamlModel],
        b: StrBytes,
        *,
        content_type: str = None,
        encoding: str = None,
        proto: ExtendedProto = None,
        allow_pickle: bool = False,
    ) -> YamlModel:
        if encoding is None:
            assume_yaml = False
        else:
            assume_yaml = ("yaml" in content_type) or ("yml" in content_type)

        if (proto == "yaml") or assume_yaml:
            try:
                obj = yaml.load(b)
            except Exception as e:
                raise ValidationError([ErrorWrapper(e, loc=ROOT_KEY)], cls)
            return cls.parse_obj(obj)
        else:
            return super().parse_raw(
                b,
                content_type=content_type,
                encoding=encoding,
                proto=proto,
                allow_pickle=allow_pickle,
            )

    @classmethod
    def parse_file(
        cls: YamlModel,
        path: Union[str, Path],
        *,
        content_type: str = None,
        encoding: str = "utf-8",
        proto: ExtendedProto = None,
        allow_pickle: bool = False,
    ) -> YamlModel:
        if encoding is None:
            assume_yaml = False
        else:
            assume_yaml = ("yaml" in content_type) or ("yml" in content_type)

        if (proto == "yaml") or assume_yaml:
            content_type = content_type or "application/yaml"
            path = Path(path)
            b = path.read_bytes()
            return cls.parse_raw(
                b,
                content_type=content_type,
                encoding=encoding,
                proto="yaml",
                allow_pickle=allow_pickle,
            )
        else:
            return super().parse_file(
                path,
                content_type=content_type,
                encoding=encoding,
                proto=proto,
                allow_pickle=allow_pickle,
            )
