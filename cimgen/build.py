# SPDX-FileCopyrightText: 2019 SOGNO
#
# SPDX-License-Identifier: Apache-2.0

import argparse
import importlib
from pathlib import Path
from types import ModuleType

from cimgen import cimgen

CGMES2 = "cgmes_v2_4_15"
CGMES3 = "cgmes_v3_0_0"
CGMES2_SCHEMA = "cgmes-application-profiles-library/CGMES/PastReleases/v2-4/Original/RDFS/*.rdf"
CGMES3_SCHEMA = "cgmes-application-profiles-library/CGMES/CurrentRelease/RDFS/*.rdf"


def build() -> None:
    parser = argparse.ArgumentParser(description="Generate some CIM classes.")
    parser.add_argument(
        "--langdir",
        type=str,
        help="The language pack directory (cpp, java, javascript, modernpython, python)",
        required=True,
    )
    parser.add_argument(
        "--cgmes_version",
        type=str,
        choices=[CGMES2, CGMES3],
        default=CGMES3,
        help="CGMES Version",
    )
    parser.add_argument("--schemadir", type=str, help="The schema directory")
    parser.add_argument("--outdir", type=str, help="The output directory")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose logging")

    args: argparse.Namespace = parser.parse_args()

    # Set default schema directory for cgmes_v2_4_15 and cgmes_v3_0_0
    if not args.schemadir:
        if args.cgmes_version == CGMES2:
            args.schemadir = CGMES2_SCHEMA
        elif args.cgmes_version == CGMES3:
            args.schemadir = CGMES3_SCHEMA

    # Set default output directory for cgmes_v2_4_15 and cgmes_v3_0_0
    if not args.outdir:
        outdir = Path("output") / args.langdir
        if args.cgmes_version == CGMES2:
            outdir /= "v2"
        elif args.cgmes_version == CGMES3:
            outdir /= "v3"
        args.outdir = str(outdir)

    if args.verbose:
        for arg, value in vars(args).items():
            if arg != "verbose":
                print(f"{arg:15}: {value}")

    lang_pack: ModuleType
    try:
        lang_pack = importlib.import_module(f"cimgen.languages.{args.langdir}.lang_pack")
    except ModuleNotFoundError:
        parser.error(f"Unsupported language: {args.langdir}")

    cimgen.cim_generate(args.schemadir, args.outdir, args.cgmes_version, lang_pack)


if __name__ == "__main__":
    build()
