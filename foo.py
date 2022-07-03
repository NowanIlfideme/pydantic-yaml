from pathlib import Path
from typing import Union
from pydantic_yaml import YamlModel
from pydantic_yaml.ext.bad_include import FileRef


path_ex = str(Path("tmp.json").absolute())


class X(YamlModel):
    a: str


class Y(YamlModel):
    b: str


Frx = FileRef[Y, X]
T = Frx(path_ex)
t = T.parse()


class Foo(YamlModel):
    xy: Union[X, Y, FileRef[X, Y]]


f1 = Foo.parse_raw(
    """
xy:
    a: aaa
"""
)

f2 = Foo.parse_raw(
    f"""
xy: !FileRef {path_ex}
"""
)

f1
f2
