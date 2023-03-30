"""Tests for file IO."""

# type: ignore

from json.decoder import JSONDecodeError
from pathlib import Path
from typing import no_type_check

import pytest


@no_type_check
def test_file_io(tmpdir: str):
    """Test file IO with temporary files (tmpdir is a pytest fixture)."""
    from pydantic import BaseModel
    from pydantic_yaml import YamlModel, YamlModelMixin, YamlStrEnum

    class MyEnum(YamlStrEnum):
        a = "a"
        b = "b"

    class MyModel(YamlModel):
        x: int = 1
        e: MyEnum = MyEnum.a

    class TestBase(BaseModel):
        tag: str = "my tag"

    class MyOtherModel(YamlModelMixin, TestBase):
        sub: MyModel

    m1 = MyModel(x=2, e="b")
    m2 = MyOtherModel(sub=m1)

    base_dir: Path = Path(tmpdir).resolve()

    for m, M in zip([m1, m2], [MyModel, MyOtherModel]):
        with (base_dir / "mdl.yaml").open(mode="w") as f:
            f.write(m.yaml())
        with (base_dir / "mdl.json").open(mode="w") as f:
            f.write(m.json())
        assert M.parse_file(base_dir / "mdl.yaml") == m
        assert M.parse_file(base_dir / "mdl.json") == m
        assert M.parse_file(base_dir / "mdl.yaml", content_type=None) == m
        assert M.parse_file(base_dir / "mdl.json", content_type=None) == m

        with pytest.raises(JSONDecodeError):
            M.parse_file(base_dir / "mdl.yaml", content_type="application/json")
        # This works because JSON is a subset of YAML :)
        mx = M.parse_file(base_dir / "mdl.json", content_type="application/yaml")
        assert mx == m
