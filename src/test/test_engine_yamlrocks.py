"""Tests for the optional `yamlrocks` engine (see issue #338).

These are skipped entirely if `yamlrocks` isn't installed, since it's an optional
dependency (`pip install pydantic-yaml[yamlrocks]`, Python >=3.12 only).
"""

from pathlib import Path

import pytest
from pydantic import BaseModel
from ruamel.yaml import YAML

pytest.importorskip("yamlrocks")

from pydantic_yaml import (  # noqa: E402
    get_default_engine,
    parse_yaml_file_as,
    parse_yaml_raw_as,
    set_default_engine,
    to_yaml_file,
    to_yaml_str,
)
from pydantic_yaml.examples.base_models import A, CommentedModel, HasEnums, UsesRefs, commented, root  # noqa: E402
from pydantic_yaml.examples.common import MyIntEnum, MyStrEnum  # noqa: E402

has_enums = HasEnums(opts=MyStrEnum.option1, vals=[MyIntEnum.v1, MyIntEnum.v2])


def clean_but_keep_newlines(s: str) -> str:
    """Remove extra spaces (but keep newlines) and drop blank lines."""
    lines = [line for line in s.splitlines() if line.strip() != ""]
    return "\n".join(" ".join(line.split()) for line in lines)


def eq_within_spaces(got: str, expected: str) -> bool:
    """Check if two strings are equal, ignoring differences in whitespace runs and blank lines."""
    return clean_but_keep_newlines(got) == clean_but_keep_newlines(expected)


@pytest.mark.parametrize(
    ["model_type", "fn"],
    [
        (A, "a.yaml"),
        (A, "a-1.1.yaml"),
        (A, "a-1.2.yaml"),
        (HasEnums, "has_enums.yaml"),
        (UsesRefs, "uses_refs.yaml"),
    ],
)
def test_load_rt_simple_files(model_type: type[BaseModel], fn: str):
    """Loading and roundtripping works the same way as the "ruamel" engine."""
    obj = parse_yaml_file_as(model_type, root / fn, engine="yamlrocks")
    raw = to_yaml_str(obj, engine="yamlrocks")
    obj_rt = parse_yaml_raw_as(model_type, raw, engine="yamlrocks")
    assert obj_rt == obj


def test_write_open_file(tmpdir):
    """Test writing to a pre-opened file, same as the "ruamel" engine."""
    with (Path(tmpdir) / "test_write_open_file.yaml").open(mode="w") as f:
        to_yaml_file(f, A(a="a"), engine="yamlrocks")


@pytest.mark.parametrize(
    ["kwargs", "expected"],
    [
        [dict(default_flow_style=False), "opts: option1\nvals:\n- 1\n- 2\n"],
        [dict(default_flow_style=True), "{opts: option1, vals: [1, 2]}\n"],
        [dict(indent=4), "opts: option1\nvals:\n    - 1\n    - 2\n"],
    ],
)
def test_dump_kwargs(kwargs: dict, expected: str):
    """Formatting kwargs behave the same as the "ruamel" engine for representable cases."""
    res = to_yaml_str(has_enums, engine="yamlrocks", **kwargs)
    assert res == expected


def test_dump_kwargs_unsupported_combo_raises():
    """Indent combinations that ruamel supports but yamlrocks can't represent raise clearly."""
    with pytest.raises(NotImplementedError):
        to_yaml_str(has_enums, indent=6, map_indent=2, engine="yamlrocks")


def test_custom_yaml_writer_rejected():
    """`custom_yaml_writer` is ruamel-specific and must be rejected for engine='yamlrocks'."""
    with pytest.raises(TypeError):
        to_yaml_str(has_enums, custom_yaml_writer=YAML(typ="safe"), engine="yamlrocks")


sub_ps = {
    False: commented / "false",
    "fields-only": commented / "fields",
    "models-only": commented / "models",
}


@pytest.mark.parametrize("add_comments", [False, "fields-only", "models-only"])
def test_add_comments_matches_ruamel_fixtures(add_comments):
    """For the (non-inconsistent) cases, comment output matches the "ruamel" engine's fixtures."""
    obj = parse_yaml_file_as(UsesRefs, root / "uses_refs.yaml", engine="yamlrocks")
    got = to_yaml_str(obj, add_comments=add_comments, engine="yamlrocks")
    expected = (sub_ps[add_comments] / "uses_refs.yaml").read_text()
    assert eq_within_spaces(got, expected)


def test_add_comments_true_includes_all_descriptions():
    """`add_comments=True` includes both model docstrings and field descriptions, at every level.

    Unlike the "ruamel" engine (see the `CommentedModel` xfail in test_comment_writing.py and
    issue #338), yamlrocks doesn't drop the nested model's docstring when the field itself also
    has a trailing description comment, so we check content directly instead of byte-matching
    the ruamel-derived fixture.
    """
    obj = parse_yaml_file_as(UsesRefs, root / "uses_refs.yaml", engine="yamlrocks")
    got = to_yaml_str(obj, add_comments=True, engine="yamlrocks")
    assert "# Example for the reference data." in got
    assert "# First/last names." in got
    assert "# Billing information" in got
    assert "# Family name(s), often called 'last name' in English." in got


def test_commented_model_smoke():
    """`CommentedModel` (docstrings, `Annotated` and attribute-docstring descriptions) roundtrips."""
    obj = parse_yaml_file_as(CommentedModel, root / "commented_model.yaml", engine="yamlrocks")
    got = to_yaml_str(obj, add_comments=True, engine="yamlrocks")
    assert "# Model for testing advanced commenting cases." in got
    assert "# See three? PO" in got


def test_engine_selection():
    """`engine="yamlrocks"` works as the explicit default, bypassing autodetection.

    See test_engine_selection.py for the (backend-independent) autodetection/env-var logic.
    """
    original = get_default_engine()
    try:
        set_default_engine("yamlrocks")
        assert get_default_engine() == "yamlrocks"
        # No engine passed -> uses the new default.
        assert to_yaml_str(A(a="a")) == to_yaml_str(A(a="a"), engine="yamlrocks")
    finally:
        set_default_engine(original)
