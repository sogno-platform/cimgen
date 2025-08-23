import chevron
import logging
import re
import shutil
from pathlib import Path
from importlib.resources import files

logger = logging.getLogger(__name__)


# Setup called only once: make output directory, create base class, create profile class, etc.
# This makes sure we have somewhere to write the classes, and
# creates a couple of files the python implementation needs.
# cgmes_profile_details contains index, names and uris for each profile.
# We use that to create the header data for the profiles.
def setup(output_path: str, version: str, cgmes_profile_details: list[dict], namespaces: dict[str, str]) -> None:
    source_dir = Path(__file__).parent
    dest_dir = Path(output_path)
    for file in dest_dir.glob("**/*.[mp]*"):
        file.unlink()
    # Add all hardcoded utils and create parent dir
    for file in source_dir.glob("utils/*.[mp]*"):
        dest_file = dest_dir / file.relative_to(source_dir)
        dest_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(file, dest_file)
    _create_constants(dest_dir, version, namespaces)
    _create_cgmes_profile(dest_dir, cgmes_profile_details)


# These are the files that are used to generate the python files.
class_template_file = {"filename": "class_template.mustache", "ext": ".py"}
constants_template_file = {"filename": "constants_template.mustache", "ext": ".py"}
profile_template_file = {"filename": "profile_template.mustache", "ext": ".py"}
enum_template_file = {"filename": "enum_template.mustache", "ext": ".py"}
primitive_template_file = {"filename": "primitive_template.mustache", "ext": ".py"}
datatype_template_file = {"filename": "datatype_template.mustache", "ext": ".py"}

partials = {}


def _get_python_type(datatype: str) -> str:
    if datatype.lower() == "integer":
        return "int"
    if datatype.lower() == "boolean":
        return "bool"
    if datatype.lower() == "datetime":
        return "datetime"
    if datatype.lower() == "date":
        return "date"
    if datatype.lower() == "time":
        return "time"
    if datatype.lower() == "monthday":
        return "str"  # TO BE FIXED? I could not find a datatype in python that holds only month and day.
    if datatype.lower() == "string":
        return "str"
    else:
        # everything else should be a float
        return "float"


def _set_datatype_attributes(attributes: list[dict]) -> dict:
    datatype_attributes = {}
    datatype_attributes["python_type"] = "None"
    import_set = set()
    for attribute in attributes:
        if "value" in attribute.get("about", "") and "attribute_class" in attribute:
            datatype_attributes["python_type"] = _get_python_type(attribute["attribute_class"])
        if "is_fixed" in attribute:
            import_set.add(attribute["attribute_class"])
    datatype_attributes["is_fixed_imports"] = sorted(import_set)
    return datatype_attributes


def get_base_class() -> str:
    return "Base"


def get_class_location(class_name: str, class_map: dict, version: str) -> str:  # NOSONAR
    # Check if the current class has a parent class
    if class_map[class_name].subclass_of() and class_map[class_name].subclass_of() in class_map:
        return f".{class_map[class_name].subclass_of()}"
    return "..utils.base"


def run_template(output_path: str, class_details: dict) -> None:

    # Add some attribute infos
    for attribute in class_details["attributes"]:
        attribute["python_type"], attribute["default_value"] = _python_type_and_default_value(attribute)

    if class_details["is_a_primitive_class"]:
        # Primitives are never used in the in memory representation but only for
        # the schema
        template = primitive_template_file
        class_details["python_type"] = _get_python_type(class_details["class_name"])
    elif class_details["is_a_datatype_class"]:
        # Datatypes based on primitives are never used in the in memory
        # representation but only for the schema
        template = datatype_template_file
        class_details.update(_set_datatype_attributes(class_details["attributes"]))
    elif class_details["is_an_enum_class"]:
        template = enum_template_file
        for instance in class_details["enum_instances"]:
            if "comment" in instance:
                if instance["label"] in ("cosPhi", "lPerl", "gPerg", "sPers", "HzPerHz", "VPerV", "APerA", "WPerW"):
                    instance["comment"] += "  # noqa: E501, RUF003"
                elif instance["label"] in ("l", "I"):
                    instance["comment"] += "  # noqa: E501, E741"
                elif instance["label"] == "count":
                    instance["comment"] += "  # noqa: E501  # type: ignore"
                else:
                    instance["comment"] += "  # noqa: E501"
    else:
        template = class_template_file
    resource_file = _create_file(output_path, class_details, template)
    _write_templated_file(resource_file, class_details, template["filename"])


def _create_file(output_path: str, class_details: dict, template: dict[str, str]) -> Path:
    resource_file = Path(output_path) / "resources" / (class_details["class_name"] + template["ext"])
    resource_file.parent.mkdir(exist_ok=True)
    return resource_file


def _write_templated_file(class_file: Path, class_details: dict, template_filename: str) -> None:
    with class_file.open("w", encoding="utf-8") as file:
        templates = files("cimgen.languages.modernpython.templates")
        with templates.joinpath(template_filename).open(encoding="utf-8") as f:
            args = {
                "data": class_details,
                "template": f,
                "partials_dict": partials,
            }
            output = chevron.render(**args)
        file.write(output)


def _create_constants(output_path: Path, version: str, namespaces: dict[str, str]) -> None:
    class_file = output_path / "utils" / ("constants" + constants_template_file["ext"])
    namespaces_list = [{"ns": ns, "uri": uri} for ns, uri in sorted(namespaces.items())]
    class_details = {"version": version, "namespaces": namespaces_list}
    _write_templated_file(class_file, class_details, constants_template_file["filename"])


def _create_cgmes_profile(output_path: Path, profile_details: list[dict]) -> None:
    class_file = output_path / "utils" / ("profile" + profile_template_file["ext"])
    class_details = {"profiles": profile_details}
    _write_templated_file(class_file, class_details, profile_template_file["filename"])


def _python_type_and_default_value(attribute: dict) -> tuple[str, str]:
    """Get the python type and the default value of the attribute.

    :param attribute:  Dictionary with information about an attribute of a class.
    :return:           Tuple containing python type and default value
    """
    if attribute["is_datatype_attribute"]:
        return ("float", "default=0.0")
    if attribute["is_enum_attribute"]:
        return ("str", 'default=""')
    if attribute["is_class_attribute"]:
        return ("Optional[str]", "default=None")
    if attribute["is_list_attribute"]:
        return ("list", "default_factory=list")
    # primitive attribute
    if attribute["attribute_class"] == "Integer":
        return ("int", "default=0")
    if attribute["attribute_class"] == "Boolean":
        return ("bool", "default=False")
    if attribute["attribute_class"] in ("Float", "Decimal"):
        return ("float", "default=0.0")
    # primitive string attribute
    return ("str", 'default=""')


def resolve_headers(path: str, version: str) -> None:
    """Add all classes in __init__.py"""

    if match := re.search(r"(?P<num>\d+_\d+_\d+)", version):  # NOSONAR
        version_number = match.group("num").replace("_", ".")
    else:
        raise ValueError(f"Cannot parse {version} to extract a number.")

    src = Path(__file__).parent / "templates"
    dest = Path(path) / "resources"
    with open(src / "__init__.py", "r", encoding="utf-8") as template_file:
        template_text = template_file.read()
    with open(dest / "__init__.py", "a", encoding="utf-8") as header_file:
        header_file.write(template_text)
        header_file.write(f'\nCGMES_VERSION = "{version_number}"\n')

        # # Under this, add all imports in init. Disabled becasue loading 600 unneeded classes is slow.
        # _all = ["CGMES_VERSION"]

        # for include_name in sorted(dest.glob("*.py")):
        #     stem = include_name.stem
        #     if stem in[ "__init__", "Base"]:
        #         continue
        #     _all.append(stem)
        #     header_file.write(f"from .{stem} import {stem}\n")

        # header_file.write(
        #     "\n".join(
        #         [
        #             "# This is not needed per se, but by referencing all imports",
        #             "# this prevents a potential autoflake from cleaning up the whole file.",
        #             "# FYA, if __all__ is present, only what's in there will be import with a import *",
        #             "",
        #         ]
        #     )
        # )
        # header_file.write(f"__all__={_all}")
