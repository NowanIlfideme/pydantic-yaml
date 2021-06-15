import warnings

from pydantic import validator

from .models import YamlModel

try:
    from pydantic import SemVer
except ImportError:
    from ._semver import SemVer

__all__ = ["SemVer", "VersionedYamlModel"]


def _chk_between(v, lo=None, hi=None):
    if v is None:
        return
    if (hi is not None) and (v > hi):
        raise ValueError(f"Default version higher than maximum: {v} > {hi}")
    if (lo is not None) and (v < lo):
        raise ValueError(f"Default version lower than minimum: {v} < {lo}")


class VersionedYamlModel(YamlModel):
    """YAML model with versioning.
    
    By default, the "version" field checks between 
    `Config.min_version` and `Config.max_version`, if those are not None.

    It's best not to even set the `version` field by hand.
    """

    version: SemVer

    def __init_subclass__(cls) -> None:
        fld = cls.__fields__["version"]
        d = fld.default
        if d is None:
            pass
        else:
            _chk_between(d, lo=cls.Config.min_version, hi=cls.Config.max_version)
            warnings.warn(
                f"Recommended to have `version` be required, but set default {d!r}",
                UserWarning,
            )

        if not issubclass(fld.type_, SemVer):
            raise TypeError(
                f"Field type for `version` must be SemVer, got {fld.type_!r}"
            )

    @validator("version", always=True)
    def _check_semver(cls, v):
        _chk_between(v, lo=cls.Config.min_version, hi=cls.Config.max_version)
        return v

    class Config:
        min_version = SemVer("0.0.0")
        max_version = None
