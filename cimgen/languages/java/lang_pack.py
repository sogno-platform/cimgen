import chevron
import shutil
from pathlib import Path
from importlib.resources import files
from typing import Callable


# Setup called only once: make output directory, create base class, create profile class, etc.
# This just makes sure we have somewhere to write the classes.
# cgmes_profile_details contains index, names and uris for each profile.
# We use that to create the header data for the profiles.
def setup(output_path: str, version: str, cgmes_profile_details: list[dict], namespaces: dict[str, str]) -> None:
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
    _create_cgmes_profile(dest_dir, cgmes_profile_details)


# These are the files that are used to generate the java files.
# There is a template set for the large number of classes that are floats. They
# have unit, multiplier and value attributes in the schema, but only appear in
# the file as a float string.
class_template_file = {"filename": "java_class.mustache", "ext": ".java"}
float_template_file = {"filename": "java_float.mustache", "ext": ".java"}
enum_template_file = {"filename": "java_enum.mustache", "ext": ".java"}
string_template_file = {"filename": "java_string.mustache", "ext": ".java"}
constants_template_file = {"filename": "java_constants.mustache", "ext": ".java"}
profile_template_file = {"filename": "java_profile.mustache", "ext": ".java"}
classlist_template_file = {"filename": "java_classlist.mustache", "ext": ".java"}

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


def _create_cgmes_profile(output_path: Path, profile_details: list[dict]) -> None:
    class_file = output_path / ("CGMESProfile" + profile_template_file["ext"])
    class_details = {"profiles": profile_details}
    _write_templated_file(class_file, class_details, profile_template_file["filename"])


# This function just allows us to avoid declaring a variable called 'switch',
# which is in the definition of the ExcBBC class.
def label(text: str, render: Callable[[str], str]) -> str:
    result = render(text)
    if result == "switch":
        return "_switch"
    else:
        return result


# The code below this line is used after the main cim_generate phase to generate CimClassMap.java.

class_blacklist = [
    "AttributeInterface",
    "BaseClassInterface",
    "BaseClassBuilder",
    "PrimitiveBuilder",
    "BaseClass",
    "CGMESProfile",
    "CimClassMap",
    "CimConstants",
    "Logging",
]


def resolve_headers(path: str, version: str) -> None:  # NOSONAR
    directory = Path(path)
    classlist_file = directory / ("CimClassMap" + classlist_template_file["ext"])
    classes = []
    for file in sorted(directory.glob("*.java"), key=lambda f: f.stem):
        class_name = file.stem
        if class_name not in class_blacklist:
            classes.append(class_name)
    _write_templated_file(classlist_file, {"classes": classes}, classlist_template_file["filename"])
