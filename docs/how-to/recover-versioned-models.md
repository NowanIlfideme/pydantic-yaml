# Recover Versioned Models

`pydantic-yaml` used to ship a built-in "versioned model" feature. It was removed - its
usefulness for most users was questionable, and it pulled in a `semver` dependency for
everyone, whether they used it or not. See
[Breaking changes across versions](../explanation/changelog.md) for the full history.

If you need the behavior back, below is a self-contained, Pydantic v2 implementation you can
drop into your own project - it validates a `version` field against a per-subclass min/max
range, and requires only `semver` (`pip install semver`) as an extra dependency:

```python
"""Versioned model example (Pydantic v2).

Library versions:

    pydantic>=2
    semver~=3.0.0  # additional, not a pydantic-yaml dependency
"""

from typing import Any, ClassVar

from pydantic import BaseModel, ConfigDict, field_serializer, field_validator
from semver import Version


def _chk_between(v: Version, lo: Version | None, hi: Version | None) -> None:
    if hi is not None and v > hi:
        raise ValueError(f"Version higher than maximum: {v} > {hi}")
    if lo is not None and v < lo:
        raise ValueError(f"Version lower than minimum: {v} < {lo}")


class VersionedModel(BaseModel):
    """Base model that validates a `version` field against a per-subclass min/max range."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    version: Version

    min_version: ClassVar[Version] = Version(0, 0, 0)
    max_version: ClassVar[Version | None] = None

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """Normalize and validate the subclass's `min_version`/`max_version`."""
        super().__init_subclass__(**kwargs)
        if isinstance(cls.min_version, str):
            cls.min_version = Version.parse(cls.min_version)
        if isinstance(cls.max_version, str):
            cls.max_version = Version.parse(cls.max_version)
        if cls.max_version is not None and cls.min_version > cls.max_version:
            raise ValueError(
                f"Minimum version higher than maximum: {cls.min_version!r} > {cls.max_version!r}"
            )

    @field_validator("version", mode="before")
    @classmethod
    def _parse_version(cls, v: Any) -> Version:
        """Parse `version` from a string, then check it's within `[min_version, max_version]`."""
        if not isinstance(v, Version):
            v = Version.parse(v)
        _chk_between(v, lo=cls.min_version, hi=cls.max_version)
        return v

    @field_serializer("version")
    def _serialize_version(self, v: Version) -> str:
        """Dump `version` as a plain string, e.g. for YAML/JSON output."""
        return str(v)
```

Subclass it and set `min_version`/`max_version` as class variables (a plain string works too -
`__init_subclass__` parses it):

```python
from typing import ClassVar
from semver import Version
from pydantic_yaml import parse_yaml_raw_as, to_yaml_str

class FooBar(VersionedModel):
    """Foobar model."""

    foo: str
    max_version: ClassVar[Version] = Version(1)

fb = parse_yaml_raw_as(FooBar, "version: 0.2.0\nfoo: bar\n")
print(to_yaml_str(fb))
# version: 0.2.0
# foo: bar

# A version above max_version fails validation, as expected:
parse_yaml_raw_as(FooBar, "version: 1.2.0\nfoo: bar\n")
# pydantic.ValidationError: 1 validation error for FooBar
# version
#   Value error, Version higher than maximum: 1.2.0 > 1.0.0 [type=value_error, ...]
```
