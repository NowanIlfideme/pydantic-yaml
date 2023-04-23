# Versioned Models

Versioned models were removed from `pydantic-yaml` as their usefulness for most
users was questionable, and it added the `semver` dependency.

If you need to recover functionality, below is an alternative you should use
that is almost pure Pydantic v1.

## Custom VersionedModel in Pydantic v1

```python
"""Versioned model example.

Library versions:

    pydantic<2
    semver~=3.0.0  # additional
"""

import warnings
from typing import Optional, Tuple, Type

from pydantic import BaseModel, validator
from semver import Version  # type: ignore


def _chk_between(v, lo=None, hi=None):
    if v is None:
        return
    if (hi is not None) and (v > hi):
        raise ValueError(f"Default version higher than maximum: {v} > {hi}")
    if (lo is not None) and (v < lo):
        raise ValueError(f"Default version lower than minimum: {v} < {lo}")


def _get_minmax_robust(
    cls: Type["VersionedModel"],
) -> Tuple[Optional[Version], Optional[Version]]:
    min_, max_ = None, None
    for supcls in cls.mro():
        Config = getattr(supcls, "Config", None)
        if Config is not None:
            if min_ is None:
                min_ = getattr(Config, "min_version", None)
            if max_ is None:
                max_ = getattr(Config, "max_version", None)
    return min_, max_


class VersionedModel(BaseModel):
    """Versioned model behavior."""

    version: Version

    class Config:
        """Pydantic configuration."""

        # Allow SemVer
        arbitrary_types_allowed = True
        json_encoders = {Version: lambda x: str(x)}

        # Version limits
        min_version = Version(0, 0, 0)
        max_version = None

    @validator("version", pre=True)
    def _check_version(cls: Type["VersionedModel"], v) -> Version:  # type: ignore
        """Set version from a string, then check within the limits."""
        if not isinstance(v, Version):
            v = Version.parse(v)

        min_, max_ = _get_minmax_robust(cls)
        _chk_between(v, lo=min_, hi=max_)
        return v

    def __init_subclass__(cls) -> None:
        """Set config values."""
        # Check Config class types
        Config = getattr(cls, "Config", None)
        if Config is not None:
            # check one field
            minv = getattr(Config, "min_version", None)
            if minv is not None:
                if not isinstance(minv, Version):
                    setattr(Config, "min_version", Version.parse(minv))
            # check other field
            maxv = getattr(Config, "max_version", None)
            if maxv is not None:
                if not isinstance(maxv, Version):
                    setattr(Config, "max_version", Version.parse(maxv))

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

        if not issubclass(fld.type_, Version):
            raise TypeError(f"Field type for `version` must be Version, got {fld.type_!r}")


if __name__ == "__main__":
    from pydantic_yaml import parse_yaml_raw_as

    class FooBar(VersionedModel):
        """Foobar model."""

        foo: str

        class Config:
            """Pydantic configuration."""

            max_version = Version(1)

    fb = parse_yaml_raw_as(
        FooBar,
        """
        version: 0.2.0
        foo: bar
        """,
    )
    try:
        parse_yaml_raw_as(
            FooBar,
            """
            version: 1.2.0  # higher than v1!
            foo: bar
            """,
        )
    except Exception as e:
        print(e)


```
