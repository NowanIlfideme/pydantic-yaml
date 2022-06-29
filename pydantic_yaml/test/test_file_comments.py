"""Tests for file comments."""

# type: ignore

from json.decoder import JSONDecodeError
from pathlib import Path
from typing import no_type_check, List

import pytest


@no_type_check
def test_file_comments(tmpdir: str):
    """Test file IO with temporary files (tmpdir is a pytest fixture)."""

    from pydantic import BaseModel, Field
    from pydantic_yaml import YamlModel, YamlModelMixin, YamlStrEnum

    class MyEnum(YamlStrEnum):
        a = "a"
        b = "b"

    class MyModel(YamlModel):
        x: int = Field(42, description="This is an important description")
        e: MyEnum = Field(MyEnum.a, description="doubletest")

    class TestBase(BaseModel):
        tag: str = "my tag"

    class MyOtherModel(YamlModelMixin, TestBase):
        sub: MyModel = Field(None, description="Mymodel description")
        sublist: List[MyModel] = [MyModel()]

    m2 = MyOtherModel(sub=MyModel(x="41"), sublist=[MyModel(),MyModel(x="43",e="b")])

    base_dir: Path = Path(tmpdir).resolve()

    for (m, M) in zip([m2], [MyOtherModel]):
        with (base_dir / "mdl.yaml").open(mode="w") as f:
            f.write(m.yaml(descriptions = True))
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

        with open(base_dir / "mdl.yaml", "r") as f:
            text = f.read()
            assert('This is an important description' in text)
            assert('doubletest' in text)
            assert('Mymodel description' in text)

