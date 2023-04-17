"""Basic tests for the README examples."""


def test_readme_basic_usage():
    """Basic usage example from README."""
    from enum import Enum
    from pydantic import BaseModel, validator
    from pydantic_yaml import parse_yaml_raw_as, to_yaml_str

    class MyEnum(str, Enum):
        """A custom enumeration that is YAML-safe."""

        a = "a"
        b = "b"

    class InnerModel(BaseModel):
        """A normal pydantic model that can be used as an inner class."""

        fld: float = 1.0

    class MyModel(BaseModel):
        """Our custom class, with a `.yaml()` method.

        The `parse_raw()` and `parse_file()` methods are also updated to be able to
        handle `content_type='application/yaml'`, `protocol="yaml"` and file names
        ending with `.yml`/`.yaml`
        """

        x: int = 1
        e: MyEnum = MyEnum.a
        m: InnerModel = InnerModel()

        @validator("x")
        def _chk_x(cls, v: int) -> int:  # noqa
            """You can add your normal pydantic validators, like this one."""
            assert v > 0
            return v

    m1 = MyModel(x=2, e="b", m=InnerModel(fld=1.5))

    # This dumps to YAML and JSON respectively
    yml = to_yaml_str(m1)
    jsn = m1.json()

    # This parses YAML as the MyModel type
    m2 = parse_yaml_raw_as(MyModel, yml)
    assert m1 == m2

    # JSON is also valid YAML, so this works too
    m3 = parse_yaml_raw_as(MyModel, jsn)
    assert m1 == m3
