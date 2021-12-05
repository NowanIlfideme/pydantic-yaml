"""Basic tests for pydantic_yaml functionality."""


def test_readme():
    """Tests the functionality from the README."""

    from pydantic_yaml import YamlStrEnum, YamlModel

    class MyEnum(YamlStrEnum):
        a = "a"
        b = "b"

    class MyModel(YamlModel):
        x: int = 1
        e: MyEnum = MyEnum.a

    m1 = MyModel(x=2, e="b")
    yml = m1.yaml()
    jsn = m1.json()

    # This automatically assumes YAML
    m2 = MyModel.parse_raw(yml)
    assert m1 == m2

    # This explicitly sets YAML (or `content_type="application/yaml"`)
    m3 = MyModel.parse_raw(yml, proto="yaml")
    assert m1 == m3

    # This explicitly uses JSON
    m4 = MyModel.parse_raw(jsn, content_type="application/json")
    assert m1 == m4

    # JSON is actually a subset of YAML, so it should parse correctly anyways.
    m5 = MyModel.parse_raw(jsn)
    assert m1 == m5


def test_nested_models():
    """Test nested YAML models and inheritance."""

    from pydantic import BaseModel
    from pydantic_yaml import YamlModel, YamlModelMixin

    class A0(BaseModel):
        x: int = 1

    class A(A0, YamlModelMixin):
        x: int = 1

    class B(BaseModel):
        y: str = "hello"

    class C(YamlModel):
        a: A
        b: B

    c = C(a=A(x=11), b=B(y="bye"))

    yml = c.yaml()

    c_re = C.parse_raw(yml, proto="yaml")
    assert c == c_re


# def test_files():
#     """TODO: Test with tempfiles."""
