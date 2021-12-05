from pydantic import BaseModel

from .mixin import YamlModelMixin

_pre_doc = """`pydantic.BaseModel` class with built-in YAML support.

You can alternatively inherit from `(pydantic.BaseModel, pydantic_yaml.YamlModelMixin)`
to implement your model.

See Also
--------
pydantic-yaml: https://github.com/NowanIlfideme/pydantic-yaml
pydantic: https://pydantic-docs.helpmanual.io/
pyyaml: https://pyyaml.org/
ruamel.yaml: https://yaml.readthedocs.io/en/latest/index.html
"""


class YamlModel(YamlModelMixin, BaseModel):
    __doc__ = _pre_doc + BaseModel.__doc__
