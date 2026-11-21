# SPDX-FileCopyrightText: 2026 SOGNO
#
# SPDX-License-Identifier: Apache-2.0

from typing import Any

import pytest

from cimgen.cimgen import RDFSEntry, _clean_comments


@pytest.mark.parametrize(
    "input_data, expected",
    [
        ("SimpleString", "SimpleString"),
        (
            {"$rdf:resource": "http://iec.ch/TC57/CIM#ActivePower"},
            "http://iec.ch/TC57/CIM#ActivePower",
        ),
        (
            {"$rdf:about": "#IdentifiedObject"},
            "#IdentifiedObject",
        ),
        (
            {"$rdfs:Literal": "iec61970cim16v28"},
            "iec61970cim16v28",
        ),
        (
            ["FirstString", "SecondString"],
            "FirstString",
        ),
    ],
)
def test_extract_string(input_data: Any, expected: str) -> None:
    assert RDFSEntry._extract_string(input_data) == expected


@pytest.mark.parametrize(
    "input_data, expected",
    [
        (
            {"_": "Description of the element"},
            "Description of the element",
        ),
        (
            {"$rdfs:Literal": "iec61970cim16v28"},
            "iec61970cim16v28",
        ),
        (
            {"_": "Preferred text", "$rdfs:Literal": "Secondary text"},
            "Preferred text",
        ),
        (
            [{"_": "First comment"}, {"_": "Second comment"}],
            "First comment",
        ),
        (
            {"$someAttr": "value"},
            "",
        ),
    ],
)
def test_extract_text(input_data: Any, expected: str) -> None:
    assert RDFSEntry._extract_text(input_data) == expected


@pytest.mark.parametrize(
    "input_text, expected",
    [
        ("", ""),
        ("Simple text", "Simple text"),
        ('<rdfs:label xml:lang="en">voltage</rdfs:label>', '<rdfs:label xml:lang="en">voltage</rdfs:label>'),
        (
            '<rdfs:comment  rdf:parseType="Literal">Type of input signal.</rdfs:comment>',
            '<rdfs:comment  rdf:parseType="Literal">Type of input signal.</rdfs:comment>',
        ),
        (
            '<rdfs:comment  rdf:parseType="Literal">Valve positioner (<i>A</i>).</rdfs:comment>',
            '<rdfs:comment  rdf:parseType="Literal">Valve positioner (A).</rdfs:comment>',
        ),
        (
            '<rdfs:comment  rdf:parseType="Literal">General wind turbine Q control modes <i>M</i><sub>qG</sub>.</rdfs:comment>',  # noqa: E501
            '<rdfs:comment  rdf:parseType="Literal">General wind turbine Q control modes MqG.</rdfs:comment>',
        ),
        (
            """
            <rdf:Description rdf:about="#GovHydroIEEE0.k">
                <rdfs:label xml:lang="en">k</rdfs:label>
                <rdfs:comment  rdf:parseType="Literal">Governor gain (K<i>)</i>.</rdfs:comment>
            </rdf:Description>
            """,
            """
            <rdf:Description rdf:about="#GovHydroIEEE0.k">
                <rdfs:label xml:lang="en">k</rdfs:label>
                <rdfs:comment  rdf:parseType="Literal">Governor gain (K).</rdfs:comment>
            </rdf:Description>
            """,
        ),
    ],
)
def test_clean_comments(input_text: str, expected: str) -> None:
    assert _clean_comments(input_text) == expected
