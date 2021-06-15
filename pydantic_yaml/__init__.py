import warnings as _w

try:
    from .main import __version__, YamlEnum, YamlModel
except Exception as e:
    _w.warn(str(e))
