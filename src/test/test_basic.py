"""Tests for basic functionality."""

from typing import Type

import pydantic
import pytest
from pydantic import BaseModel

from pydantic_yaml import parse_yaml_file_as, parse_yaml_raw_as, to_yaml_str
from pydantic_yaml.examples.base_models import (
    A,
    B,
    CustomRootListObj,
    CustomRootListStr,
    Empty,
    HasEnums,
    SecretTstModel,
    SecretTstModelDumpable,
    UsesRefs,
    root,
)


@pytest.mark.parametrize(
    ["model_type", "fn"],
    [
        (Empty, "a.yaml"),
        (A, "a.yaml"),
        (A, "a-1.1.yaml"),
        (A, "a-1.2.yaml"),
        (B, "b.yaml"),
        (UsesRefs, "uses_refs.yaml"),
        (HasEnums, "has_enums.yaml"),
        (CustomRootListStr, "root_list_str.yaml"),
        (CustomRootListObj, "root_list_obj.yaml"),
    ],
)
def test_load_rt_simple_files(model_type: Type[BaseModel], fn: str):
    """Test simple file loading and roundtripping."""
    # Load file
    file = root / fn
    obj = parse_yaml_file_as(model_type, file)
    # Roundtrip
    raw = to_yaml_str(obj)
    obj_rt = parse_yaml_raw_as(model_type, raw)
    # Check equality
    assert obj_rt == obj


@pytest.mark.parametrize("model", [A(a="aaa")])
def test_write_simple_model(model: BaseModel):
    """Test output of simple models."""
    to_yaml_str(model)  # TODO: Check output vs expected?


@pytest.mark.xfail(pydantic.__version__ >= "2", reason="Pydantic v2 is stricter for Bytes types.")
def test_secret_no_rt():
    """Test secret models properly failing to roundtrip."""
    sm = SecretTstModel(ss="123", sb=b"321")  # type: ignore
    assert sm.ss.get_secret_value() == "123"
    assert sm.sb.get_secret_value() == b"321"

    raw = to_yaml_str(sm)
    mdl = parse_yaml_raw_as(SecretTstModel, raw)
    assert mdl.ss.get_secret_value() != "123"
    assert mdl.sb.get_secret_value() != b"321"


@pytest.mark.xfail(pydantic.__version__ >= "2", reason="Pydantic v2 is stricter for Bytes types.")
def test_secret_yes_rt():
    """Test 'fixed' secret models properly roundtripping."""
    sm = SecretTstModelDumpable(ss="123", sb=b"321")  # type: ignore
    assert sm.ss.get_secret_value() == "123"
    assert sm.sb.get_secret_value() == b"321"

    raw = to_yaml_str(sm)
    mdl = parse_yaml_raw_as(SecretTstModelDumpable, raw)
    assert mdl.ss.get_secret_value() == "123"
    assert mdl.sb.get_secret_value() == b"321"
