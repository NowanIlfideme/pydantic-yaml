"""Tests proving the `YamlReader`/`YamlWriter` protocols are genuinely third-party-extensible.

This is the concrete proof for the milestone's "even dumping by hand" ask (see issue #338 and
the custom-yaml-engine milestone): a custom reader/writer needs no inheritance from anything in
`pydantic_yaml`, and doesn't need to go through JSON at all if it doesn't want to.
"""

import json
from io import IOBase
from typing import Any

from pydantic import BaseModel, ConfigDict

from pydantic_yaml import YamlEngine, YamlReader, YamlWriter, parse_yaml_raw_as, to_yaml_str


class Point(BaseModel):
    """A simple model to round-trip through custom readers/writers."""

    x: int
    y: int
    label: str = "origin"


class PlainClassEngine:
    """A custom reader+writer as a single plain class.

    No inheritance, no Pydantic, no external library. Dumps "by hand": walks the model's own
    fields directly, never touching JSON or any YAML library at all (writes a trivial
    `key: value` line format that happens to also be valid YAML, to keep this test
    self-contained). Implementing both `read`/`write` on one object - rather than a matched pair
    of classes like the built-ins - is exactly what the `YamlEngine` convenience protocol is for.
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
    """A custom reader+writer as a frozen Pydantic model, exactly like the built-ins.

    Proves the protocols don't require anything pydantic-yaml-specific either, just the methods.
    """

    model_config = ConfigDict(frozen=True)

    def read(self, stream: IOBase) -> Any:
        """Parse via plain `json.loads` - JSON is valid YAML."""
        return json.loads(stream.read())

    def write(self, stream: IOBase, model: BaseModel) -> None:
        """Write via plain `model_dump_json` - no YAML library involved at all."""
        stream.write(model.model_dump_json())


def test_plain_class_engine_satisfies_protocols():
    """A plain class with `read`/`write` methods satisfies `YamlReader`/`YamlWriter`/`YamlEngine`."""
    engine = PlainClassEngine()
    assert isinstance(engine, YamlReader)
    assert isinstance(engine, YamlWriter)
    assert isinstance(engine, YamlEngine)


def test_pydantic_model_engine_satisfies_protocols():
    """A Pydantic-model-based reader+writer also satisfies the protocols - no special-casing needed."""
    engine = PydanticEngine()
    assert isinstance(engine, YamlReader)
    assert isinstance(engine, YamlWriter)
    assert isinstance(engine, YamlEngine)


def test_plain_class_engine_round_trips():
    """A hand-written, JSON-free custom reader/writer works end-to-end through the public API."""
    engine = PlainClassEngine()
    p = Point(x=1, y=2, label="hi")
    dumped = to_yaml_str(p, writer=engine)
    assert dumped == "x: 1\ny: 2\nlabel: hi\n"
    back = parse_yaml_raw_as(Point, dumped, reader=engine)
    assert back == p


def test_pydantic_model_engine_round_trips():
    """A Pydantic-model-based custom reader/writer works end-to-end through the public API."""
    engine = PydanticEngine()
    p = Point(x=3, y=4)
    dumped = to_yaml_str(p, writer=engine)
    back = parse_yaml_raw_as(Point, dumped, reader=engine)
    assert back == p
