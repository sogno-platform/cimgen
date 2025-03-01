import chevron
import shutil
from pathlib import Path
from importlib.resources import files
from typing import Callable


# Setup called only once: make output directory, create base class, create profile class, etc.
# This just makes sure we have somewhere to write the classes.
# cgmes_profile_details contains index, names and uris for each profile.
# We don't use that here because we aren't exporting into
# separate profiles.
def setup(
    output_path: str, version: str, cgmes_profile_details: list[dict], namespaces: dict[str, str]
) -> None:  # NOSONAR
    source_dir = Path(__file__).parent
    dest_dir = Path(output_path)
    for file in dest_dir.glob("**/*.java"):
        file.unlink()
    # Add all hardcoded utils and create parent dir
    for file in source_dir.glob("**/*.java"):
        dest_file = dest_dir / file.relative_to(source_dir)
        dest_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(file, dest_file)
    _create_constants(dest_dir, version, namespaces)


# These are the files that are used to generate the java files.
# There is a template set for the large number of classes that are floats. They
# have unit, multiplier and value attributes in the schema, but only appear in
# the file as a float string.
class_template_file = {"filename": "java_class.mustache", "ext": ".java"}
float_template_file = {"filename": "java_float.mustache", "ext": ".java"}
enum_template_file = {"filename": "java_enum.mustache", "ext": ".java"}
string_template_file = {"filename": "java_string.mustache", "ext": ".java"}
constants_template_file = {"filename": "java_constants.mustache", "ext": ".java"}

partials = {
    "label": "{{#lang_pack.label}}{{label}}{{/lang_pack.label}}",
}


def get_base_class() -> str:
    return "BaseClass"


def get_class_location(class_name: str, class_map: dict, version: str) -> str:  # NOSONAR
    return ""


# This is the function that runs the template.
def run_template(output_path: str, class_details: dict) -> None:

    if class_details["is_a_datatype_class"] or class_details["class_name"] in ("Float", "Decimal"):
        template = float_template_file
    elif class_details["is_an_enum_class"]:
        template = enum_template_file
    elif class_details["is_a_primitive_class"]:
        template = string_template_file
    else:
        template = class_template_file

    if class_details["class_name"] in ("Integer", "Boolean"):
        # These classes are defined already
        # We have to implement operators for them
        return

    class_file = Path(output_path) / (class_details["class_name"] + template["ext"])
    _write_templated_file(class_file, class_details, template["filename"])


def _write_templated_file(class_file: Path, class_details: dict, template_filename: str) -> None:
    with class_file.open("w", encoding="utf-8") as file:
        templates = files("cimgen.languages.java.templates")
        with templates.joinpath(template_filename).open(encoding="utf-8") as f:
            args = {
                "data": class_details,
                "template": f,
                "partials_dict": partials,
            }
            output = chevron.render(**args)
        file.write(output)


def _create_constants(output_path: Path, version: str, namespaces: dict[str, str]) -> None:
    class_file = output_path / ("CimConstants" + constants_template_file["ext"])
    namespaces_list = [{"ns": ns, "uri": uri} for ns, uri in sorted(namespaces.items())]
    class_details = {"version": version, "namespaces": namespaces_list}
    _write_templated_file(class_file, class_details, constants_template_file["filename"])


# This function just allows us to avoid declaring a variable called 'switch',
# which is in the definition of the ExcBBC class.
def label(text: str, render: Callable[[str], str]) -> str:
    result = render(text)
    if result == "switch":
        return "_switch"
    else:
        return result


# The code below this line is used after the main cim_generate phase to generate CIMClassMap.java.

class_blacklist = [
    "AttributeInterface",
    "BaseClassInterface",
    "BaseClassBuilder",
    "PrimitiveBuilder",
    "BaseClass",
    "CIMClassMap",
    "CimConstants",
    "Logging",
]


def _create_header_include_file(
    directory: Path,
    header_include_filename: str,
    header: list[str],
    footer: list[str],
    before: str,
    after: str,
    blacklist: list[str],
) -> None:
    lines = []
    for file in sorted(directory.glob("*.java"), key=lambda f: f.stem):
        basename = file.stem
        if basename not in blacklist:
            lines.append(before + 'Map.entry("' + basename + '", new cim4j.' + basename + after + "),\n")
    lines[-1] = lines[-1].replace("),", ")")
    for line in lines:
        header.append(line)
    for line in footer:
        header.append(line)
    header_include_filepath = directory / header_include_filename
    with header_include_filepath.open("w", encoding="utf-8") as f:
        f.writelines(header)


def resolve_headers(path: str, version: str) -> None:  # NOSONAR
    class_list_header = [
        "/*\n",
        "Generated from the CGMES files via cimgen: https://github.com/sogno-platform/cimgen\n",
        "*/\n",
        "package cim4j;\n",
        "import java.util.Map;\n",
        "public class CIMClassMap {\n",
        "	public static boolean isCIMClass(java.lang.String key) {\n",
        "		return classMap.containsKey(key);\n",
        "	}\n",
        "	public static Map<java.lang.String, BaseClass> classMap = Map.ofEntries(\n",
    ]
    class_list_footer = ["	);\n", "}\n"]

    _create_header_include_file(
        Path(path),
        "CIMClassMap.java",
        class_list_header,
        class_list_footer,
        "		",
        "()",
        class_blacklist,
    )
