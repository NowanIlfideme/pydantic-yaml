"""Imports an installed YAML library."""

# flake8: noqa

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


__all__ = ["yaml", "__yaml_lib__"]
