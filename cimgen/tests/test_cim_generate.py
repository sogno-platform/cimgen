# SPDX-FileCopyrightText: 2026 SOGNO
#
# SPDX-License-Identifier: Apache-2.0

import base64
import hashlib
from pathlib import Path

from cimgen.cimgen import cim_generate
from cimgen.languages.java import lang_pack

CGMES2 = "cgmes_v2_4_15"
CGMES3 = "cgmes_v3_0_0"
CGMES2_SCHEMA = "cgmes-application-profiles-library/CGMES/PastReleases/v2-4/Original/RDFS"
CGMES3_SCHEMA = "cgmes-application-profiles-library/CGMES/CurrentRelease/RDFS"


def test_cim_generate_java_cgmes2(tmp_path: Path) -> None:
    cim_generate_java(tmp_path, CGMES2, CGMES2_SCHEMA, "h1:mv//7v6ZNmLO2QJ/SypnHjuEm5tcKHquke/ypeCo9mc=")


def test_cim_generate_java_cgmes3(tmp_path: Path) -> None:
    cim_generate_java(tmp_path, CGMES3, CGMES3_SCHEMA, "h1:/w6CnsI8u0woxYRtDd45nOxIfK7dU5j1H1PYsISjDFQ=")


def cim_generate_java(tmp_path: Path, version: str, schema: str, expected_hash: str) -> None:
    """
    CIM code generation test for language java
    """
    root = Path(__file__).parent.parent.parent
    schema_path = (root / schema).resolve()
    print(f"Schema directory: {schema_path}")

    output_path = tmp_path / "output_java"
    print(f"Generated source files in: {output_path}")

    cim_generate(schema_path, str(output_path), version, lang_pack)

    # Test directory hash
    dir_hash = compute_dirhash_h1(output_path)
    assert dir_hash == expected_hash


def compute_dirhash_h1(dir: Path) -> str:
    """
    Python implementatation of Go's dirhash.Hash1 (golang.org/x/mod/sumdb/dirhash)
    """
    files_dict: dict[str, Path] = {}
    for file in dir.rglob("*"):
        if file.is_file():
            rel_path: str = str(file.relative_to(dir).as_posix())
            files_dict[rel_path] = file

    lines: list[str] = []
    for rel_path, file in sorted(files_dict.items()):
        content = file.read_bytes()
        hash = hashlib.sha256(content).hexdigest()
        lines.append(f"{hash}  {rel_path}\n")

    summary = "".join(lines).encode("utf-8")
    top_hash = base64.b64encode(hashlib.sha256(summary).digest()).decode("ascii")
    return f"h1:{top_hash}"
