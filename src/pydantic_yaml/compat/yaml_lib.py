"""Imports an installed YAML library."""

# flake8: noqa

from typing import Any, Optional
from io import BytesIO, StringIO, IOBase


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
            "Could not import ruamel.yaml or pyyaml, " "please install at least one of them."
        )

dumper_classes = []
for _fld in dir(yaml):
    try:
        if "Dumper" in _fld:
            _obj = getattr(yaml, _fld)
            dumper_classes.append(_obj)
    except Exception:
        pass

representer_classes = []
for _fld in dir(yaml):
    try:
        if "Representer" in _fld:
            _obj = getattr(yaml, _fld)
            representer_classes.append(_obj)
    except Exception:
        pass


def yaml_safe_load(stream) -> Any:
    """Wrapper around YAML library loader."""
    if __yaml_lib__ in ["ruamel-old", "pyyaml"]:
        return yaml.safe_load(stream)
    # Fixing deprecation warning in new ruamel.yaml versions
    assert __yaml_lib__ == "ruamel-new"
    ruamel_obj = yaml.YAML(typ="safe", pure=True)
    if isinstance(stream, str):
        return ruamel_obj.load(StringIO(stream))
    elif isinstance(stream, bytes):
        return ruamel_obj.load(BytesIO(stream))
    # we hope it's a stream, but don't enforce it
    return ruamel_obj.load(stream)


def yaml_safe_dump(data: Any, stream=None, *, sort_keys: bool = False, **kwds) -> Optional[Any]:
    """Wrapper around YAML library dumper.

    Parameters
    ----------
    data
        The data you want to dump, typically a mapping (dict).
    stream
        The stream to dump to. By default (if no stream is given, i.e. None),
        this will instead dump to a text stream.
    sort_keys : bool
        Whether to sort the keys of mappings before dumping.
        Default value is False, rather than True, which is the YAML default.
        This is because Pydantic configs are easier to read if dumped in the
        same order as they are defined.
    kwds
        Other keyword arguments to set on the YAML dumper instance.
    """
    if __yaml_lib__ in ["ruamel-old", "pyyaml"]:
        return yaml.safe_dump(data, stream=stream, sort_keys=sort_keys, **kwds)
    # Fixing deprecation warning in new ruamel.yaml versions
    assert __yaml_lib__ == "ruamel-new"
    ruamel_obj = yaml.YAML(typ="safe", pure=True)
    ruamel_obj.sort_base_mapping_type_on_output = sort_keys  # type: ignore
    # Hacking some options that aren't available
    for kw in ["encoding", "default_flow_style", "default_style", "indent"]:
        if kw in kwds:
            setattr(ruamel_obj, kw, kwds[kw])

    if stream is None:
        text_stream = StringIO()
        ruamel_obj.dump(data, stream=text_stream)
        text_stream.seek(0)  # otherwise we always get ''
        return text_stream.read()
    else:
        ruamel_obj.dump(data, stream=stream)
        return None


__all__ = ["yaml_safe_dump", "yaml_safe_load", "yaml", "__yaml_lib__"]
