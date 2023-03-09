"""Tests for SecretStr, SecretBytes."""

import pytest
from pydantic import SecretBytes, SecretStr

from pydantic_yaml import YamlModel


class SecretTstModel(YamlModel):
    """Normal model with secret fields."""

    ss: SecretStr
    sb: SecretBytes


def test_secret_types_no_rt():
    """Basic tests for SecretStr, SecretBytes not being dumped.

    Note that we actually intend to lose data when saving!
    """
    # Create model
    sm = SecretTstModel(ss="123", sb="321")
    assert sm.ss.get_secret_value() == "123"
    assert sm.sb.get_secret_value() == b"321"

    # Roundtrip (should technically work)
    y = sm.yaml()
    mdl = SecretTstModel.parse_raw(y)

    # Hey, we don't have the same values roundtrip!
    # These should be "**********", but let's not be exact - styling can change. :)
    assert mdl.ss.get_secret_value() != "123"
    assert mdl.sb.get_secret_value() != b"321"


class SecretTstModelDumpable(SecretTstModel):
    """Round-trippable model.

    TODO: Support YAML encoders? Or just use the JSON encoders instead?
    """

    class Config:
        json_encoders = {
            SecretStr: lambda v: v.get_secret_value() if v else None,
            SecretBytes: lambda v: v.get_secret_value() if v else None,
        }


@pytest.mark.xfail(reason="YAML/JSON encoder support doesn't exist yet.")
def test_secret_types_roundtrippable():
    """Tests roundtrippability when encoders are specified."""
    # Create newer model
    sd = SecretTstModelDumpable(ss="123", sb="321")
    y = sd.yaml()
    sd2 = SecretTstModelDumpable.parse_raw(y)
    sm_alt = SecretTstModel.parse_raw(y)

    assert sd2 == sd
    assert sm_alt.ss.get_secret_value() == sd.ss.get_secret_value()
    assert sm_alt.sb.get_secret_value() == sd.sb.get_secret_value()
