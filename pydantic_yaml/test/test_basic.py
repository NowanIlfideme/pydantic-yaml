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

    m2 = MyModel.parse_raw(yml)  # This automatically assumes YAML
    assert m1 == m2

    m3 = MyModel.parse_raw(jsn)  # This will fallback to JSON
    assert m1 == m3

    m4 = MyModel.parse_raw(yml, proto="yaml")
    assert m1 == m4

    m5 = MyModel.parse_raw(yml, content_type="application/yaml")
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
