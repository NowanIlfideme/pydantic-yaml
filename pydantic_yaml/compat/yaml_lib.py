"""Imports an installed YAML library."""

# flake8: noqa

from typing import Any, Optional


try:
    import ruamel.yaml as yaml  # type: ignore

    # ruamel.yaml doesn't have type annotations

    if yaml.__version__ < "0.15.0":
        __yaml_lib__ = "ruamel-old"
    else:
        __yaml_lib__ = "ruamel-new"
except ImportError:
    try:
        import yaml  # type: ignore

        __yaml_lib__ = "pyyaml"
    except ImportError:
        raise ImportError(
            "Could not import ruamel.yaml or pyyaml, "
            "please install at least one of them."
        )

dumper_classes = []
for _fld in dir(yaml):
    try:
        if "Dumper" in _fld:
            _obj = getattr(yaml, _fld)
            dumper_classes.append(_obj)
    except Exception:
        pass


def yaml_safe_load(stream) -> Any:
    """Wrapper around YAML library loader."""
    if __yaml_lib__ in ["ruamel-old", "pyyaml"]:
        return yaml.safe_load(stream)
    # Fixing deprecation warning in new ruamel.yaml versions
    assert __yaml_lib__ == "ruamel-new"
    ruamel_obj = yaml.YAML(typ="safe", pure=True)
    return ruamel_obj.load(stream)


def yaml_safe_dump(data: Any, stream=None, **kwds) -> Optional[Any]:
    """Wrapper around YAML library dumper."""
    if __yaml_lib__ in ["ruamel-old", "pyyaml"]:
        return yaml.safe_dump(data, stream=stream, **kwds)
    # Fixing deprecation warning in new ruamel.yaml versions
    assert __yaml_lib__ == "ruamel-new"
    ruamel_obj = yaml.YAML(typ="safe", pure=True)
    return ruamel_obj.dump(data, stream=stream, **kwds)


__all__ = ["yaml_safe_dump", "yaml_safe_load", "yaml", "__yaml_lib__"]
