from typing import Optional, Tuple, Type
import warnings

from pydantic import validator

from pydantic_yaml.model import YamlModel
from .semver import SemVer

__all__ = ["VersionedYamlModel"]


def _chk_between(v, lo=None, hi=None):
    if v is None:
        return
    if (hi is not None) and (v > hi):
        raise ValueError(f"Default version higher than maximum: {v} > {hi}")
    if (lo is not None) and (v < lo):
        raise ValueError(f"Default version lower than minimum: {v} < {lo}")


def _get_minmax_robust(
    cls: Type["VersionedYamlModel"],
) -> Tuple[Optional[SemVer], Optional[SemVer]]:
    min_, max_ = None, None
    for supcls in cls.mro():
        Config = getattr(supcls, "Config", None)
        if Config is not None:
            if min_ is None:
                min_ = getattr(Config, "min_version", None)
            if max_ is None:
                max_ = getattr(Config, "max_version", None)
    return min_, max_


class VersionedYamlModel(YamlModel):
    """YAML model with versioning support.

    Usage
    -----
    Inherit from this class, and set a Config class with attributes
    `min_version` and/or `max_version`:

    ```python
    class MyModel(VersionedYamlModel):
        class Config:
            min_version = "1.0.0"

        foo: str = "bar"
    ```

    By default, the minimum version is "0.0.0" and the maximum is unset.
    This pattern enables you to more easily version your YAML files and
    protect against accidentally using older (or newer) configuration file formats.

    Notes
    -----
    By default, a validator checks that the "version" field is between
    `Config.min_version` and `Config.max_version`, if those are not None.

    It's probably best not to even set the `version` field by hand, but rather
    in your configuration.
    """

    version: SemVer

    def __init_subclass__(cls) -> None:
        # Check Config class types
        Config = getattr(cls, "Config", None)
        if Config is not None:
            # check one field
            minv = getattr(Config, "min_version", None)
            if minv is not None:
                if not isinstance(minv, SemVer):
                    setattr(Config, "min_version", SemVer(minv))
            # check other field
            maxv = getattr(Config, "max_version", None)
            if maxv is not None:
                if not isinstance(maxv, SemVer):
                    setattr(Config, "max_version", SemVer(maxv))

        # Check ranges
        min_, max_ = _get_minmax_robust(cls)
        if (min_ is not None) and (max_ is not None) and (min_ > max_):
            raise ValueError(f"Minimum version higher than maximum: {min_!r} > {max_!r}")

        # Check the default value of the "version" field
        fld = cls.__fields__["version"]
        d = fld.default
        if d is None:
            pass
        else:
            _chk_between(d, lo=min_, hi=max_)
            warnings.warn(
                f"Recommended to have `version` be required, but set default {d!r}",
                UserWarning,
            )

        if not issubclass(fld.type_, SemVer):
            raise TypeError(f"Field type for `version` must be SemVer, got {fld.type_!r}")

    @validator("version", always=True)
    def _check_semver(cls, v):
        min_, max_ = _get_minmax_robust(cls)
        _chk_between(v, lo=min_, hi=max_)
        return v

    class Config:
        min_version = SemVer("0.0.0")
        max_version = None
