from pathlib import Path
from typing import Union
from typing import Any, Dict, Optional, Type, TypeVar

from pydantic import ValidationError, parse_file_as, parse_obj_as, root_validator
from pydantic_yaml import YamlModel
from pydantic_yaml.ext.include import BaseInclude, FileInclude, AllowReferences

path_ex = str(Path("tmp.json").absolute())


class X(YamlModel):
    a: str


class Y(YamlModel):
    b: str


class Foo(AllowReferences, YamlModel):
    xy: Union[X, Y, FileInclude]

    @root_validator()
    def _load_references(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        """Loads external references."""
        assert issubclass(cls, YamlModel)
        values = values.copy()
        updates = {}
        for k, v in values.items():
            if isinstance(v, str):
                fld = cls.__fields__[k]
                try:
                    v = parse_obj_as(fld.type_, v)
                except ValidationError:
                    continue
                if isinstance(v, BaseInclude):
                    updates[k] = v.load_reference()
        values.update(updates)
        return values


f1 = Foo.parse_raw(
    """
xy:
    a: aaa
"""
)

f2 = Foo.parse_raw(
    f"""
xy: include {path_ex}
"""
)

f1
f2
