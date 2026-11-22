# SPDX-FileCopyrightText: 2019 SOGNO
#
# SPDX-License-Identifier: Apache-2.0

import argparse
import importlib
from types import ModuleType

from cimgen import cimgen

CGMES2 = "cgmes_v2_4_15"
CGMES3 = "cgmes_v3_0_0"
CGMES2_SCHEMA = "cgmes-application-profiles-library/CGMES/PastReleases/v2-4/Original/RDFS/*.rdf"
CGMES3_SCHEMA = "cgmes-application-profiles-library/CGMES/CurrentRelease/RDFS/*.rdf"


def build() -> None:
    parser = argparse.ArgumentParser(description="Generate some CIM classes.")
    parser.add_argument(
        "--lang",
        type=str,
        help="The target language (cpp, java, javadb, js, python, python-simple)",
        required=True,
    )
    parser.add_argument(
        "--version",
        type=str,
        choices=[CGMES2, CGMES3],
        default=CGMES3,
        help="CGMES Version",
    )
    parser.add_argument(
        "--schema",
        type=str,
        help="The glob pattern for CIM schema files (or several patterns, separated by commas)",
    )
    parser.add_argument("--output", type=str, help="The output directory")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose logging")

    args: argparse.Namespace = parser.parse_args()

    # Set default schema pattern for cgmes_v2_4_15 and cgmes_v3_0_0
    if not args.schema:
        if args.version == CGMES2:
            args.schema = CGMES2_SCHEMA
        elif args.version == CGMES3:
            args.schema = CGMES3_SCHEMA

    # Set default output directory for cgmes_v2_4_15 and cgmes_v3_0_0
    if not args.output:
        args.output = "output/" + args.lang
        if args.version == CGMES2:
            args.output += "/v2"
        elif args.version == CGMES3:
            args.output += "/v3"

    if args.verbose:
        for arg, value in vars(args).items():
            if arg != "verbose":
                print(f"{arg:15}: {value}")

    lang_pack: ModuleType
    lang = args.lang.replace("-", "_")  # "-" not allowed in python identifiers
    try:
        lang_pack = importlib.import_module(f"cimgen.languages.{lang}.lang_pack")
    except ModuleNotFoundError:
        parser.error(f"Unsupported language: {args.lang}")

    cimgen.cim_generate(args.schema, args.output, args.version, lang_pack)


if __name__ == "__main__":
    build()
