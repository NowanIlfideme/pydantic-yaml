def test_readme():
    """Tests the functionality from the README."""

    from pydantic_yaml import YamlEnum, YamlModel

    class MyEnum(str, YamlEnum):
        a = "a"
        b = "b"

    class MyModel(YamlModel):
        x: int = 1
        e: MyEnum = MyEnum.a

    m1 = MyModel(x=2, e="b")
    yml = m1.yaml()

    m2 = MyModel.parse_raw(yml, proto="yaml")
    assert m1 == m2

    m3 = MyModel.parse_raw(yml, content_type="application/yaml")
    assert m1 == m3
