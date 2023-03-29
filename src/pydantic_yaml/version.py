"""Gets the version, either installed or dynamically."""

__all__ = ["__version__"]

from importlib_metadata import PackageNotFoundError, version  # noqa

try:
    from setuptools_scm import get_version

    __version__ = get_version(root="../..", relative_to=__file__)
except Exception:
    try:
        __version__ = version("pydantic_yaml")
    except PackageNotFoundError:
        __version__ = "0.0.0"
