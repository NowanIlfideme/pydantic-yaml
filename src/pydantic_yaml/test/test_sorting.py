"""Tests ability to have keys 'unsorted' (in field definition order)."""


def test_sorting():
    from pydantic_yaml import YamlModel

    class B(YamlModel):
        val: str = "val"

    class X(YamlModel):
        c: str = "c"
        b: B = B()
        a: int = 1

    x = X()
    assert x.yaml(sort_keys=False) == "c: c\nb:\n  val: val\na: 1\n"
    assert x.yaml(sort_keys=True) == "a: 1\nb:\n  val: val\nc: c\n"
