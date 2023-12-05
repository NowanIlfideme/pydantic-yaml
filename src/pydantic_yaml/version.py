"""Gets the version, either installed or dynamically."""

__all__ = ["__version__"]


def __get_version() -> str:
    try:
        from setuptools_scm import get_version  # noqa

        vv = get_version(root="../..", relative_to=__file__)
    except Exception:
        import importlib.metadata as _im

        try:
            vv = _im.version("pydantic_yaml")
        except _im.PackageNotFoundError:
            vv = "0.0.0"
    return vv


__version__ = __get_version()
