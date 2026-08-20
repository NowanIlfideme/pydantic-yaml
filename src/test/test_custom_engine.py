"""Tests proving the `YamlEngine` protocol is genuinely third-party-extensible.

This is the concrete proof for the milestone's "even dumping by hand" ask (see issue #338 and
the custom-yaml-engine milestone): a custom engine needs no inheritance from anything in
`pydantic_yaml`, and doesn't need to go through JSON at all if it doesn't want to.
"""

import json
from io import IOBase
from typing import Any

from pydantic import BaseModel, ConfigDict

from pydantic_yaml import YamlEngine, parse_yaml_raw_as, to_yaml_str


class Point(BaseModel):
    """A simple model to round-trip through custom engines."""

    x: int
    y: int
    label: str = "origin"


class PlainClassEngine:
    """A custom engine as a plain class - no inheritance, no Pydantic, no external library.

    Dumps "by hand": walks the model's own fields directly, never touching JSON or any YAML
    library at all (writes a trivial `key: value` line format that happens to also be valid
    YAML, to keep this test self-contained).
    """

    def read(self, stream: IOBase) -> Any:
        """Parse the hand-rolled `key: value` line format back into a dict."""
        data: dict[str, Any] = {}
        for line in stream.read().splitlines():
            if not line.strip():
                continue
            key, _, value = line.partition(":")
            value = value.strip()
            data[key.strip()] = int(value) if value.lstrip("-").isdigit() else value
        return data

    def write(self, stream: IOBase, model: BaseModel) -> None:
        """Write the model's fields as `key: value` lines, straight off the instance."""
        for name in type(model).model_fields:
            stream.write(f"{name}: {getattr(model, name)}\n")


class PydanticEngine(BaseModel):
    """A custom engine as a frozen Pydantic model, exactly like the built-ins.

    Proves the protocol doesn't require anything pydantic-yaml-specific either, just the two
    methods.
    """

    model_config = ConfigDict(frozen=True)

    def read(self, stream: IOBase) -> Any:
        """Parse via plain `json.loads` - JSON is valid YAML."""
        return json.loads(stream.read())

    def write(self, stream: IOBase, model: BaseModel) -> None:
        """Write via plain `model_dump_json` - no YAML library involved at all."""
        stream.write(model.model_dump_json())


def test_plain_class_engine_satisfies_protocol():
    """A plain class with `read`/`write` methods satisfies `isinstance(x, YamlEngine)`."""
    assert isinstance(PlainClassEngine(), YamlEngine)


def test_pydantic_model_engine_satisfies_protocol():
    """A Pydantic-model-based engine also satisfies the protocol - no special-casing needed."""
    assert isinstance(PydanticEngine(), YamlEngine)


def test_plain_class_engine_round_trips():
    """A hand-written, JSON-free custom engine works end-to-end through the public API."""
    engine = PlainClassEngine()
    p = Point(x=1, y=2, label="hi")
    dumped = to_yaml_str(p, engine=engine)
    assert dumped == "x: 1\ny: 2\nlabel: hi\n"
    back = parse_yaml_raw_as(Point, dumped, engine=engine)
    assert back == p


def test_pydantic_model_engine_round_trips():
    """A Pydantic-model-based custom engine works end-to-end through the public API."""
    engine = PydanticEngine()
    p = Point(x=3, y=4)
    dumped = to_yaml_str(p, engine=engine)
    back = parse_yaml_raw_as(Point, dumped, engine=engine)
    assert back == p
