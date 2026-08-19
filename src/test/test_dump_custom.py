"""Test custom dumping behavior."""

import pytest

from pydantic_yaml import EngineName, to_yaml_str
from pydantic_yaml.examples.base_models import HasEnums
from pydantic_yaml.examples.common import MyIntEnum, MyStrEnum

has_enums = HasEnums(opts=MyStrEnum.option1, vals=[MyIntEnum.v1, MyIntEnum.v2])


@pytest.mark.parametrize(
    ["kwargs", "expected"],
    [
        [dict(default_flow_style=False), "opts: option1\nvals:\n- 1\n- 2\n"],
        [dict(default_flow_style=True), "{opts: option1, vals: [1, 2]}\n"],
        [dict(indent=4), "opts: option1\nvals:\n    - 1\n    - 2\n"],
    ],
)
def test_dump_kwargs(engine: EngineName, kwargs: dict, expected: str):
    """Test dumping keyword arguments; behaves identically on both engines."""
    res = to_yaml_str(has_enums, engine=engine, **kwargs)
    assert res == expected


def test_dump_kwargs_independent_map_and_sequence_indent_ruamel_only():
    """Independently-configurable `map_indent`/`sequence_indent` is a "ruamel"-only feature."""
    expected = "opts: option1\nvals:\n      - 1\n      - 2\n"
    assert to_yaml_str(has_enums, indent=6, map_indent=2, engine="ruamel") == expected

    pytest.importorskip("yamlrocks")
    with pytest.raises(NotImplementedError):
        to_yaml_str(has_enums, indent=6, map_indent=2, engine="yamlrocks")


def test_custom_yaml_writer_is_ruamel_only():
    """`custom_yaml_writer` is a "ruamel"-only feature; it's rejected for engine="yamlrocks"."""
    from ruamel.yaml import YAML

    writer = YAML(typ="safe")
    writer.default_flow_style = True
    expected = "{opts: option1, vals: [1, 2]}\n"
    got = to_yaml_str(has_enums, default_flow_style=None, custom_yaml_writer=writer, engine="ruamel")
    assert got == expected

    pytest.importorskip("yamlrocks")
    with pytest.raises(TypeError):
        to_yaml_str(has_enums, custom_yaml_writer=writer, engine="yamlrocks")
