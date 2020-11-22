# flake8: noqa

try:
    import ruamel.yaml as yaml

    if yaml.__version__ < "0.15.0":
        __yaml_lib__ = "ruamel-old"
    else:
        __yaml_lib__ = "ruamel-new"
except ImportError:
    try:
        import yaml

        __yaml_lib__ = "pyyaml"
    except ImportError:
        raise ImportError(
            "Could not import ruamel.yaml or pyyaml, "
            "please install at least one of them."
        )

__all__ = ["yaml", "__yaml_lib__"]
