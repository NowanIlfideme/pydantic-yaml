"""Gets the version, either installed or dynamically."""

__all__ = ["__version__"]


try:
    from setuptools_scm import get_version  # noqa

    __version__ = get_version(root="../..", relative_to=__file__)
except Exception:
    try:
        import importlib.metadata as _im  # noqa
    except ImportError:
        import importlib_metadata as _im  # noqa

    try:
        __version__ = _im.version("pydantic_yaml")
    except _im.PackageNotFoundError:  # type: ignore
        __version__ = "0.0.0"
