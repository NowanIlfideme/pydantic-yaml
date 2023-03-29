"""Gets the version, either installed or dynamically."""

__all__ = ["__version__"]

from typing import no_type_check


@no_type_check
def __get_version() -> str:
    try:
        from setuptools_scm import get_version  # noqa

        vv = get_version(root="../..", relative_to=__file__)
    except Exception:
        try:
            import importlib.metadata as _im  # noqa
        except ImportError:
            import importlib_metadata as _im  # noqa

        try:
            vv = _im.version("pydantic_yaml")
        except _im.PackageNotFoundError:  # noqa
            vv = "0.0.0"
    return vv


__version__ = __get_version()
