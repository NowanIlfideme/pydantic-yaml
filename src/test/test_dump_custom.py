"""Test custom dumping behavior."""

import pytest

from pydantic_yaml import RuamelEngine, YamlRocksEngine, to_yaml_str
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
def test_dump_kwargs(engine: RuamelEngine | YamlRocksEngine, kwargs: dict, expected: str):
    """Test engine formatting fields; behaves identically on both built-in engines."""
    configured = engine.model_copy(update=kwargs)
    res = to_yaml_str(has_enums, engine=configured)
    assert res == expected


def test_dump_kwargs_independent_map_and_sequence_indent_ruamel_only():
    """Independently-configurable `map_indent`/`sequence_indent` is a `RuamelEngine`-only feature.

    `YamlRocksEngine` doesn't even have these fields, so constructing one with them raises a
    Pydantic `ValidationError` (extra field) regardless of whether `yamlrocks` is installed.
    """
    expected = "opts: option1\nvals:\n      - 1\n      - 2\n"
    assert to_yaml_str(has_enums, engine=RuamelEngine(indent=6, map_indent=2)) == expected

    with pytest.raises(ValueError):
        YamlRocksEngine(indent=6, map_indent=2)  # ty: ignore[unknown-argument]


def test_custom_yaml_writer_is_ruamel_only():
    """`writer` (equivalent of the old `custom_yaml_writer`) is a `RuamelEngine`-only field."""
    from ruamel.yaml import YAML

    writer = YAML(typ="safe")
    writer.default_flow_style = True
    expected = "{opts: option1, vals: [1, 2]}\n"
    got = to_yaml_str(has_enums, engine=RuamelEngine(default_flow_style=None, writer=writer))
    assert got == expected

    with pytest.raises(ValueError):
        YamlRocksEngine(writer=writer)  # ty: ignore[unknown-argument]
