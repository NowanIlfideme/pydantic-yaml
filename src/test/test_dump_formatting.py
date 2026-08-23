"""Tests for field-order preservation (#217) and block-literal multiline strings (#34).

Both are unconditional defaults on both built-in writers - see issue #338's milestone and the
`RuamelWriter`/`YamlRocksWriter` docstrings.
"""

from typing import Annotated

import pytest
from pydantic import BaseModel, Field

from pydantic_yaml import RuamelReader, RuamelWriter, YamlRocksReader, YamlRocksWriter, YamlWriter
from pydantic_yaml import parse_yaml_raw_as, to_yaml_str


class OrderedFields(BaseModel):
    """Model with deliberately non-alphabetical field declaration order."""

    z_first: str
    a_second: str


class HasMultilineText(BaseModel):
    """Model with a plain multiline string field."""

    title: str
    body: str


class HasDescribedMultilineText(BaseModel):
    """Model whose multiline field also carries a field description."""

    notes: Annotated[str, Field(description="A note field")]


def test_field_order_preserved_by_default(writer: YamlWriter):
    """Dumping preserves declaration order, not alphabetical order (fixes #217)."""
    m = OrderedFields(z_first="one", a_second="two")
    assert to_yaml_str(m, writer=writer) == "z_first: one\na_second: two\n"


def test_sort_keys_restores_alphabetical_order(writer: RuamelWriter | YamlRocksWriter):
    """`sort_keys=True` opts back into alphabetical ordering."""
    m = OrderedFields(z_first="one", a_second="two")
    configured = writer.model_copy(update={"sort_keys": True})
    assert to_yaml_str(m, writer=configured) == "a_second: two\nz_first: one\n"


def test_multiline_string_dumps_as_block_literal(backend):
    r"""Multiline strings dump block-literal (`|`), not quoted with an escaped `\n` (fixes #34)."""
    m = HasMultilineText(title="t", body="line one\nline two\n")
    dumped = to_yaml_str(m, writer=backend.writer)
    assert "body: |" in dumped
    assert "\\n" not in dumped
    round_tripped = parse_yaml_raw_as(HasMultilineText, dumped, reader=backend.reader)
    assert round_tripped == m


def test_flow_style_multiline_string_falls_back_to_quoted_on_both_engines():
    """A multiline string can't stay block-literal under genuine flow style (`|` is block-only).

    Both writers consistently fall back to a quoted/escaped string instead of one special-casing
    block style for just that scalar. Both still round-trip.
    """
    m = HasMultilineText(title="t", body="line one\nline two\n")

    ruamel_dumped = to_yaml_str(m, writer=RuamelWriter(default_flow_style=True))
    assert "body: |" not in ruamel_dumped
    assert "\\n" in ruamel_dumped
    assert parse_yaml_raw_as(HasMultilineText, ruamel_dumped, reader=RuamelReader()) == m

    pytest.importorskip("yamlrocks")
    yr_dumped = to_yaml_str(m, writer=YamlRocksWriter(default_flow_style=True))
    assert "body: |" not in yr_dumped
    assert "\\n" in yr_dumped
    assert parse_yaml_raw_as(HasMultilineText, yr_dumped, reader=YamlRocksReader()) == m


def test_add_comments_with_multiline_field(backend):
    """A field with both a description and a multiline value.

    The comment placement is a known, cosmetic quirk (identical on both backends - the
    description can't sit on the `field: |` line since the value spans multiple lines), but
    data integrity and the comment's presence are preserved.
    """
    m = HasDescribedMultilineText(notes="line one\nline two\n")
    configured = backend.writer.model_copy(update={"add_comments": True})
    dumped = to_yaml_str(m, writer=configured)
    assert "A note field" in dumped
    round_tripped = parse_yaml_raw_as(HasDescribedMultilineText, dumped, reader=backend.reader)
    assert round_tripped == m
