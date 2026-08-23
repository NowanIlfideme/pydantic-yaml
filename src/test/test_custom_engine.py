"""Tests proving the `YamlReader`/`YamlWriter` protocols are genuinely third-party-extensible.

This is the concrete proof for the milestone's "even dumping by hand" ask (see issue #338 and
the custom-yaml-engine milestone): a custom reader/writer needs no inheritance from anything in
`pydantic_yaml`, and doesn't need to go through JSON at all if it doesn't want to. Since both
protocols are expressed via `__call__`, a plain function satisfies them just as well as a class
instance.
"""

import json
from io import IOBase
from typing import Any

from pydantic import BaseModel, ConfigDict

from pydantic_yaml import YamlReader, YamlWriter, parse_yaml_raw_as, to_yaml_str


class Point(BaseModel):
    """A simple model to round-trip through custom readers/writers."""

    x: int
    y: int
    label: str = "origin"


def plain_function_reader(stream: IOBase) -> Any:
    """Parse a hand-rolled `key: value` line format back into a dict.

    A bare function - dumps "by hand": never touches JSON or any YAML library at all (the format
    happens to also be valid YAML, to keep this test self-contained).
    """
    data: dict[str, Any] = {}
    for line in stream.read().splitlines():
        if not line.strip():
            continue
        key, _, value = line.partition(":")
        value = value.strip()
        data[key.strip()] = int(value) if value.lstrip("-").isdigit() else value
    return data


def plain_function_writer(stream: IOBase, model: BaseModel) -> None:
    """Write the model's fields as `key: value` lines, straight off the instance."""
    for name in type(model).model_fields:
        stream.write(f"{name}: {getattr(model, name)}\n")


class PydanticReader(BaseModel):
    """A custom reader as a frozen Pydantic model, exactly like the built-ins.

    Proves the protocol doesn't require anything pydantic-yaml-specific, just `__call__`.
    """

    model_config = ConfigDict(frozen=True)

    def __call__(self, stream: IOBase) -> Any:
        """Parse via plain `json.loads` - JSON is valid YAML."""
        return json.loads(stream.read())


class PydanticWriter(BaseModel):
    """A custom writer as a frozen Pydantic model, exactly like the built-ins."""

    model_config = ConfigDict(frozen=True)

    def __call__(self, stream: IOBase, model: BaseModel) -> None:
        """Write via plain `model_dump_json` - no YAML library involved at all."""
        stream.write(model.model_dump_json())


def test_plain_functions_satisfy_protocols():
    """Bare functions satisfy `YamlReader`/`YamlWriter` - no `__call__` boilerplate needed."""
    assert isinstance(plain_function_reader, YamlReader)
    assert isinstance(plain_function_writer, YamlWriter)


def test_pydantic_model_satisfies_protocols():
    """A `__call__`-based Pydantic model also satisfies the protocols - no special-casing needed."""
    reader = PydanticReader()
    writer = PydanticWriter()
    assert isinstance(reader, YamlReader)
    assert isinstance(writer, YamlWriter)


def test_plain_functions_round_trip():
    """Hand-written, JSON-free plain functions work end-to-end through the public API."""
    p = Point(x=1, y=2, label="hi")
    dumped = to_yaml_str(p, writer=plain_function_writer)
    assert dumped == "x: 1\ny: 2\nlabel: hi\n"
    back = parse_yaml_raw_as(Point, dumped, reader=plain_function_reader)
    assert back == p


def test_pydantic_model_round_trips():
    """A Pydantic-model-based custom reader/writer works end-to-end through the public API."""
    p = Point(x=3, y=4)
    dumped = to_yaml_str(p, writer=PydanticWriter())
    back = parse_yaml_raw_as(Point, dumped, reader=PydanticReader())
    assert back == p
