"""Gets the version, either installed or dynamically.

Adapted from:
https://github.com/maresb/hatch-vcs-footgun-example/blob/main/hatch_vcs_footgun_example/version.py
"""

__all__ = ["__version__"]


def __get_hatch_version() -> str:
    """Compute the most up-to-date version number in a development environment.

    For more details, see <https://github.com/maresb/hatch-vcs-footgun-example/>.
    """
    import os
    from pathlib import Path

    from hatchling.metadata.core import ProjectMetadata
    from hatchling.plugin.manager import PluginManager
    from hatchling.utils.fs import locate_file

    pyproject_toml = locate_file(__file__, "pyproject.toml")
    if pyproject_toml is None:
        raise RuntimeError("pyproject.toml not found although hatchling is installed")
    root = Path(pyproject_toml).parent

    # Temporarily set cwd to project root for PEP 517 compliance.
    old_cwd = Path.cwd()
    os.chdir(root)
    try:
        metadata = ProjectMetadata(root=str(root), plugin_manager=PluginManager())
        # Version can be static in pyproject.toml or computed dynamically:
        return metadata.core.version or metadata.hatch.version.cached
    finally:
        os.chdir(old_cwd)


def __get_importlib_metadata_version():
    """Compute the version number using importlib.metadata.

    This is the official Pythonic way to get the version number of an installed
    package. However, it is only updated when a package is installed. Thus, if a
    package is installed in editable mode, and a different version is checked out,
    then the version number will not be updated.
    """
    from importlib.metadata import version

    if __package__ is None:
        raise RuntimeError(
            f"__package__ not set in '{__file__}' - ensure that you are running this "
            "module as part of a package, e.g. 'python -m mypackage.version' instead "
            "of 'python mypackage/version.py'."
        )
    __version__ = version(__package__)
    return __version__


def __get_version() -> str:
    try:
        return __get_hatch_version()
    except Exception:
        try:
            return __get_importlib_metadata_version()
        except Exception:
            return "0.0.0"


__version__ = __get_version()
