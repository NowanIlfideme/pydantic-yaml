"""Tests ability to have keys 'unsorted' (in field definition order)."""


def test_sorting():
    from pydantic_yaml import YamlModel

    class X(YamlModel):
        c: str = "c"
        b: str = "b"
        a: int = 1

    x = X()
    assert x.yaml(sort_keys=False) == "c: c\nb: b\na: 1\n"
    assert x.yaml(sort_keys=True) == "a: 1\nb: b\nc: c\n"
