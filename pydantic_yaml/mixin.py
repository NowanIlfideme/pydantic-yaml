"""Module to define the YamlModelMixin."""

from typing_extensions import Literal
import warnings
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    Callable,
    ClassVar,
    Optional,
    Type,
    TypeVar,
    Union,
    cast,
    no_type_check,
)
from pydantic.parse import Protocol, load_file, load_str_bytes
from pydantic.main import ROOT_KEY, BaseModel, ModelMetaclass, BaseConfig
from pydantic.error_wrappers import ErrorWrapper, ValidationError
from pydantic.types import StrBytes

if TYPE_CHECKING:
    from pydantic.typing import (
        DictStrAny,
        AbstractSetIntStr,
        MappingIntStrAny,
    )

    Model = TypeVar("Model", bound="BaseModel")

from .compat.yaml_lib import yaml_safe_dump, yaml_safe_load


ExtendedProto = Union[Protocol, Literal["yaml"]]

YamlStyle = Union[
    None,
    Literal[""],
    Literal['"'],
    Literal["'"],
    Literal["|"],
    Literal[">"],
]


def is_yaml_requested(
    content_type: Optional[str] = None,
    proto: Optional[ExtendedProto] = None,
    path_suffix: Optional[str] = None,
) -> bool:
    """Checks whether YAML is requested by the user, depending on params."""
    is_yaml = False
    if content_type is not None:
        is_yaml = ("yaml" in content_type) or ("yml" in content_type)
    if proto is not None:
        is_yaml = is_yaml or (proto == "yaml")
    if path_suffix is not None:
        is_yaml = is_yaml or (path_suffix in [".yaml", ".yml"])
    return is_yaml


class YamlModelMixinConfig:
    """Additional configuration for YamlModelMixin."""

    yaml_loads: Callable[[str], Any] = yaml_safe_load  # type: ignore
    yaml_dumps: Callable[..., str] = yaml_safe_dump  # type: ignore


class YamlModelMixin(metaclass=ModelMetaclass):
    """Mixin to add YAML compatibility to your class.

    Usage
    -----
    Inherit from this and a `pydantic.BaseModel` or a subclass, like this:

    ```python
    class MyBaseType(BaseModel):
        my_field: str = "default"

    class MyExtType(YamlModelMixin, MyBaseType):
        other_field: int = 42
    ```

    `YamlModelMixin` *must* be *before* any class that inherits from
    `pydantic.BaseModel` due to issues with the method resolution order.

    You can now use `MyExtType().yaml()` to dump the class values (default here)
    to a YAML string.
    """

    if TYPE_CHECKING:
        __custom_root_type__: ClassVar[bool] = False
        __config__: ClassVar[Type[BaseConfig]] = YamlModelMixinConfig  # type: ignore

    @no_type_check
    def __init_subclass__(cls) -> None:
        super().__init_subclass__()

        # Set the config class
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
        include: Union["AbstractSetIntStr", "MappingIntStrAny", None] = None,
        exclude: Union["AbstractSetIntStr", "MappingIntStrAny", None] = None,
        by_alias: bool = False,
        skip_defaults: Optional[bool] = None,
        exclude_unset: bool = False,
        exclude_defaults: bool = False,
        exclude_none: bool = False,
        sort_keys: bool = False,
        default_flow_style: Optional[bool] = False,
        default_style: YamlStyle = None,
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
        sort_keys : bool
            If True, will sort the keys in alphanumeric order for dictionaries.
            Default is False, which will dump in the field definition order.
        default_flow_style : bool or None
            Whether to use the "flow" style in the dumper. By default, this is False,
            which uses the "block" style (probably the most familiar to users).
        default_style : {None, "", "'", '"', "|", ">"}
            This is the default style for quoting strings, used by `ruamel.yaml` dumper.
            Default is None, which varies the style based on line length.
        indent, encoding, kwargs
            Additional arguments for the dumper.
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
                " This may not work as expected. If so, please create a GitHub issue:"
                " https://github.com/NowanIlfideme/pydantic-yaml/issues/new"
            )
        cfg = cast(YamlModelMixinConfig, self.__config__)
        return cfg.yaml_dumps(
            data,
            sort_keys=sort_keys,
            default_flow_style=default_flow_style,
            default_style=default_style,
            encoding=encoding,
            indent=indent,
            **kwargs,
        )

    @no_type_check
    @classmethod
    def parse_raw(
        cls: Type["Model"],
        b: StrBytes,
        *,
        content_type: str = "application/yaml",  # This is a reasonable default, right?
        encoding: str = "utf-8",
        proto: ExtendedProto = None,
        allow_pickle: bool = False,
    ) -> "Model":
        # NOTE: Type checking this function is a PITA, because we're overriding
        # BaseModel.parse_raw, but not inheriting it due to the MRO problem!

        # Check whether we're specifically asked to parse YAML
        is_yaml = is_yaml_requested(content_type=content_type, proto=proto)

        # Note that JSON is a subset of the YAML 1.2 spec, so we should be OK
        # even if JSON is passed. It will be slower, however.
        if is_yaml:
            try:
                cfg = cast(YamlModelMixinConfig, cls.__config__)
                obj = cfg.yaml_loads(b)
            except RecursionError as e:
                raise ValueError(
                    "YAML files with recursive references are unsupported."
                ) from e
            except ValidationError:
                raise
            except Exception as e:
                raise ValidationError([ErrorWrapper(e, loc=ROOT_KEY)], cls) from e
        else:
            obj = load_str_bytes(
                b,
                proto=proto,
                content_type=content_type,
                encoding=encoding,
                allow_pickle=allow_pickle,
                json_loads=cls.__config__.json_loads,
            )
        res = cls.parse_obj(obj)  # type: ignore
        return cast("Model", res)

    @no_type_check
    @classmethod
    def parse_file(
        cls: Type["Model"],
        path: Union[str, Path],
        *,
        content_type: str = None,
        encoding: str = "utf-8",
        proto: ExtendedProto = None,
        allow_pickle: bool = False,
    ) -> "Model":
        path = Path(path)

        # Assume YAML based on the file name, so `parse_raw()` works well below
        if (content_type is None) and (path.suffix in [".yml", ".yaml"]):
            content_type = "application/yaml"

        # Check whether we're specifically asked to parse YAML
        is_yaml = is_yaml_requested(
            content_type=content_type, proto=proto, path_suffix=path.suffix
        )

        # The first code path explicitly checks YAML compatibility.
        # We offload the rest to Pydantic.
        if is_yaml:
            b = path.read_bytes()
            return cls.parse_raw(
                b,
                content_type=content_type,
                encoding=encoding,
                proto=proto,
                allow_pickle=allow_pickle,
            )
        else:
            obj = load_file(
                path,
                proto=proto,
                content_type=content_type,
                encoding=encoding,
                allow_pickle=allow_pickle,
                json_loads=cls.__config__.json_loads,
            )
            res = cls.parse_obj(obj)  # type: ignore
            return cast("Model", res)

    @classmethod
    def __try_update_forward_refs__(cls, **localns: Any) -> None:
        """
        Same as update_forward_refs but will not raise exception
        when forward references are not defined.
        """
        try:
            if issubclass(cls, BaseModel):
                super().__try_update_forward_refs__(**localns)  # type: ignore
        except AttributeError:
            pass
