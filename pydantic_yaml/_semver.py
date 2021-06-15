from functools import wraps
from typing import Any, Callable, Optional, Union, no_type_check

from pydantic import errors
from semver import VersionInfo

__all__ = ["SemVer"]


Comparator = Callable[["SemVer", Any], bool]


def _comparator(operator: Comparator) -> Comparator:
    """Wrap a Version binary op method in a type-check."""

    @wraps(operator)
    def wrapper(self: "SemVer", other: Any) -> bool:
        if not isinstance(other, SemVer):
            try:
                other = SemVer(other)
            except Exception:
                return NotImplemented
        return operator(self, other)

    return wrapper


class SemVer(str):  # want to inherit from VersionInfo, but metaclass conflict
    """Semantic Version string for Pydantic.

    Depends on `semver>=2,<3`, see:
    https://python-semver.readthedocs.io/en/3.0.0-dev.2/install.html#release-policy
    
    Waiting to be implemented here:
    https://github.com/samuelcolvin/pydantic/discussions/2506
    """

    allow_build: bool = True
    allow_prerelease: bool = True

    __slots__ = ["_info"]

    @no_type_check
    def __new__(cls, version: Optional[str], **kwargs) -> object:
        return str.__new__(cls, cls.parse(**kwargs) if version is None else version)

    def __init__(self, version: str):
        str.__init__(version)
        self._info = VersionInfo.parse(version)

    @classmethod
    def parse(
        self,
        major: int,
        minor: int = 0,
        patch: int = 0,
        prerelease: Optional[str] = None,
        build: Optional[str] = None,
    ) -> str:
        return str(VersionInfo(major, minor, patch, prerelease, build))

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, value: Union[str]) -> "SemVer":
        vi = VersionInfo.parse(value)
        if not cls.allow_build and (vi.build is None):
            raise errors.NotNoneError()
        if not cls.allow_prerelease and (vi.prerelease is None):
            raise errors.NotNoneError()
        return cls(value)

    def __repr__(self):
        cn = type(self).__qualname__
        v = super().__repr__()
        return f"{cn}({v})"

    @property
    def info(self) -> VersionInfo:
        return self._info

    @info.setter
    def info(self, value):
        raise AttributeError("attribute 'info' is readonly")

    @property
    def major(self) -> int:
        """The major part of a version (read-only)."""
        return self._info.major

    @major.setter
    def major(self, value):
        raise AttributeError("attribute 'major' is readonly")

    @property
    def minor(self) -> int:
        """The minor part of a version (read-only)."""
        return self._info.minor

    @minor.setter
    def minor(self, value):
        raise AttributeError("attribute 'minor' is readonly")

    @property
    def patch(self) -> int:
        """The patch part of a version (read-only)."""
        return self._info.patch

    @patch.setter
    def patch(self, value):
        raise AttributeError("attribute 'patch' is readonly")

    @property
    def prerelease(self) -> Optional[str]:
        """The prerelease part of a version (read-only)."""
        return self._info.prerelease

    @prerelease.setter
    def prerelease(self, value):
        raise AttributeError("attribute 'prerelease' is readonly")

    @property
    def build(self) -> Optional[str]:
        """The build part of a version (read-only)."""
        return self._info.build

    @build.setter
    def build(self, value):
        raise AttributeError("attribute 'build' is readonly")

    def __hash__(self) -> int:
        return super.__hash__(self)  # use string hashing

    @_comparator
    def __eq__(self, other: "SemVer"):
        return self._info == other._info

    @_comparator
    def __ne__(self, other: "SemVer"):
        return self._info != other._info

    @_comparator
    def __lt__(self, other: "SemVer"):
        return self._info < other._info

    @_comparator
    def __le__(self, other: "SemVer"):
        return self._info <= other._info

    @_comparator
    def __gt__(self, other: "SemVer"):
        return self._info > other._info

    @_comparator
    def __ge__(self, other: "SemVer"):
        return self._info >= other._info

