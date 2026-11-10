# SPDX-FileCopyrightText: 2019 SOGNO
#
# SPDX-License-Identifier: Apache-2.0

import glob
import logging
import os
from importlib.resources import files

import chevron

logger = logging.getLogger(__name__)


# Setup called only once: make output directory, create base class, create profile class, etc.
# This makes sure we have somewhere to write the classes, and
# creates a couple of files the python implementation needs.
# cgmes_profile_details contains index, names and uris for each profile.
# We use that to create the header data for the profiles.
def setup(output_path: str, version: str, cgmes_profile_details: list[dict], namespaces: dict[str, str]) -> None:
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    else:
        for filename in os.listdir(output_path):
            os.remove(os.path.join(output_path, filename))
    _create_base(output_path)
    _create_constants(output_path, version, namespaces)
    _create_cgmes_profile(output_path, cgmes_profile_details)


# These are the files that are used to generate the python files.
class_template_file = {"filename": "cimpy_class_template.mustache", "ext": ".py"}
base_template_file = {"filename": "cimpy_baseclass_template.mustache", "ext": ".py"}
constants_template_file = {"filename": "cimpy_constants_template.mustache", "ext": ".py"}
profile_template_file = {"filename": "cimpy_profile_template.mustache", "ext": ".py"}
init_template_file = {"filename": "cimpy_init_template.mustache", "ext": ".py"}

partials = {}


def get_base_class() -> str:
    return "Base"


def get_class_location(class_name: str, class_map: dict, version: str) -> str:
    # Check if the current class has a parent class
    if class_map[class_name].subclass_of() and class_map[class_name].subclass_of() in class_map:
        return "cimpy." + version + "." + class_map[class_name].subclass_of()
    return "cimpy." + version + ".Base"


def run_template(output_path: str, class_details: dict) -> None:
    # Add some attribute infos
    for attribute in class_details["attributes"]:
        attribute["default_value"] = _default_value(attribute)

    if class_details["class_name"] == "String":
        return
    class_file = os.path.join(output_path, class_details["class_name"] + class_template_file["ext"])
    _write_templated_file(class_file, class_details, class_template_file["filename"])


def _write_templated_file(class_file: str, class_details: dict, template_filename: str) -> None:
    with open(class_file, "w", encoding="utf-8") as file:
        templates = files("cimgen.languages.python.templates")
        with templates.joinpath(template_filename).open(encoding="utf-8") as f:
            args = {
                "data": class_details,
                "template": f,
                "partials_dict": partials,
            }
            output = chevron.render(**args)
        file.write(output)


# creates the Base class file, all classes inherit from this class
def _create_base(output_path: str) -> None:
    class_file = os.path.join(output_path, "Base" + base_template_file["ext"])
    _write_templated_file(class_file, {}, base_template_file["filename"])


def _create_constants(output_path: str, version: str, namespaces: dict[str, str]) -> None:
    class_file = os.path.join(output_path, "CimConstants" + constants_template_file["ext"])
    namespaces_list = [{"ns": ns, "uri": uri} for ns, uri in sorted(namespaces.items())]
    class_details = {"version": version, "namespaces": namespaces_list}
    _write_templated_file(class_file, class_details, constants_template_file["filename"])


def _create_cgmes_profile(output_path: str, profile_details: list[dict]) -> None:
    class_file = os.path.join(output_path, "CGMESProfile" + profile_template_file["ext"])
    class_details = {"profiles": profile_details}
    _write_templated_file(class_file, class_details, profile_template_file["filename"])


def _default_value(attribute: dict) -> str:
    """Get the default value of the attribute.

    :param attribute:  Dictionary with information about an attribute of a class.
    :return:           Default value
    """
    if attribute["is_datatype_attribute"]:
        return "0.0"
    if attribute["is_enum_attribute"]:
        return "None"
    if attribute["is_class_attribute"]:
        return "None"
    if attribute["is_list_attribute"]:
        return "None"
    # primitive attribute
    if attribute["attribute_class"] == "Integer":
        return "0"
    if attribute["attribute_class"] == "Boolean":
        return "False"
    if attribute["attribute_class"] in ("Float", "Decimal"):
        return "0.0"
    # primitive string attribute
    return '""'


# The code below this line is used after the main cim_generate phase to generate CimClassMap.java.

class_blacklist = ["CGMESProfile", "CimConstants"]


def resolve_headers(path: str, version: str) -> None:  # NOSONAR
    """Add all classes in __init__.py"""
    init_file = path + "/__init__" + init_template_file["ext"]
    classes = []
    for file in sorted(glob.glob(path + "/*.py")):
        class_name = os.path.splitext(os.path.basename(file))[0]
        if class_name not in class_blacklist:
            classes.append(class_name)
    _write_templated_file(init_file, {"classes": classes}, init_template_file["filename"])
