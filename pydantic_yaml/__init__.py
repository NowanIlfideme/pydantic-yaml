import warnings as _w

__all__ = ["__version__", "YamlEnum", "YamlModel"]

try:
    from .main import __version__, YamlEnum, YamlModel
except Exception as e:
    _w.warn(str(e))
