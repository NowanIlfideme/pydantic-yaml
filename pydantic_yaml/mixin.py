"""Module to define the YamlModelMixin."""

from typing_extensions import Literal
import warnings
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    ClassVar,
    Optional,
    Type,
    Union,
    cast,
    no_type_check,
)

from pydantic.main import ROOT_KEY, BaseModel, ModelMetaclass, BaseConfig

if TYPE_CHECKING:
    from pydantic.typing import DictStrAny, AbstractSetIntStr, MappingIntStrAny

from .compat.yaml_lib import yaml

# class YamlModelMixin(metaclass=ModelMetaclass):
#     """Mixin to add YAML compatibility to your class."""
_YamlStyle = Union[
    None, Literal[""], Literal['"'], Literal["'"], Literal["|"], Literal[">"]
]


class YamlModelMixinConfig:
    """Additional configuration for YamlModelMixin."""

    yaml_loads: Callable[[str], Any] = yaml.safe_load  # type: ignore
    yaml_dumps: Callable[..., str] = yaml.safe_dump  # type: ignore


class YamlModelMixin(metaclass=ModelMetaclass):
    """Mixin to add YAML compatibility to your class."""

    if TYPE_CHECKING:
        __custom_root_type__: ClassVar[bool] = False
        __config__: ClassVar[Type[BaseConfig]] = YamlModelMixinConfig  # type: ignore

    @no_type_check
    def __init_subclass__(cls) -> None:
        super().__init_subclass__()
        cfg: Type[YamlModelMixinConfig] = cls.__config__
        if not issubclass(cfg, YamlModelMixinConfig):

            class T(cfg, YamlModelMixinConfig):
                pass

            T.__doc__ = cfg.__doc__
            T.__name__ = cfg.__name__
            T.__qualname__ = cfg.__qualname__

            cls.__config__ = T

    def yaml(
        self,
        *,
        include: Union["AbstractSetIntStr", "MappingIntStrAny"] = None,
        exclude: Union["AbstractSetIntStr", "MappingIntStrAny"] = None,
        by_alias: bool = False,
        skip_defaults: bool = None,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        default_flow_style: Optional[bool] = False,
        default_style: _YamlStyle = None,
        indent: Optional[bool] = None,
        encoding: Optional[str] = None,
        **kwargs,
    ) -> str:
        """Generate a YAML representation of the model.
        
        Parameters
        ----------
        include, exclude
            Fields to include or exclude. See `dict()`.
        by_alias : bool
            Whether to use aliases instead of declared names. Default is False.
        skip_defaults, exclude_unset, exclude_defaults, exclude_none
            Arguments as per `BaseModel.dict()`.
        default_flow_style : bool or None
            Whether to use the "flow" style. By default, this is False, which
            uses the "block" style (which is probably most familiar to users).
        default_style : 

        """
        data: "DictStrAny" = self.dict(  # type: ignore
            include=include,
            exclude=exclude,
            by_alias=by_alias,
            skip_defaults=skip_defaults,
            exclude_unset=exclude_unset,
            exclude_defaults=exclude_defaults,
            exclude_none=exclude_none,
        )

        if self.__custom_root_type__:
            data = data[ROOT_KEY]
            warnings.warn(
                "Explicit custom root behavior not yet implemented for pydantic_yaml."
                " This may not work as expected. If so, please create a GitHub issue!"
            )
        cfg = cast(YamlModelMixinConfig, self.__config__)
        return cfg.yaml_dumps(
            data,
            default_flow_style=default_flow_style,
            default_style=default_style,
            encoding=encoding,
            indent=indent,
            **kwargs,
        )
