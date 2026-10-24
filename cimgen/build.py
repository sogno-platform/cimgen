import argparse
import importlib
from pathlib import Path
from types import ModuleType

from cimgen import cimgen


def build() -> None:
    parser = argparse.ArgumentParser(description="Generate some CIM classes.")
    parser.add_argument("--outdir", type=str, help="The output directory", required=True)
    parser.add_argument("--schemadir", type=str, help="The schema directory", required=True)
    parser.add_argument("--langdir", type=str, help="The language pack directory", required=True)
    parser.add_argument(
        "--cgmes_version",
        type=str,
        choices=["cgmes_v2_4_13", "cgmes_v2_4_15", "cgmes_v3_0_0"],
        default="cgmes_v2_4_15",
        help="CGMES Version",
    )
    parser.add_argument(
        "--recursive",
        action="store_true",
        help="Search the schema directory recursively",
    )
    args: argparse.Namespace = parser.parse_args()

    lang_pack: ModuleType = importlib.import_module(f"cimgen.languages.{args.langdir}.lang_pack")

    schema_path: Path = Path(args.schemadir).resolve()
    if not schema_path.is_dir():
        parser.error(f"Schema directory '{schema_path}' does not exist or is not a directory.")

    cimgen.cim_generate(schema_path, args.outdir, args.cgmes_version, lang_pack, recursive=args.recursive)


if __name__ == "__main__":
    build()
