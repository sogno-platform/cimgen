import logging
import os
import re
from pathlib import Path

import chevron

logger = logging.getLogger(__name__)


# This makes sure we have somewhere to write the classes, and
# creates a couple of files the python implementation needs.
# cgmes_profile_info details which uri belongs in each profile.
# We don't use that here because we aren't creating the header
# data for the separate profiles.
def setup(version_path, cgmes_profile_info):  # NOSONAR
    if not os.path.exists(version_path):
        os.makedirs(version_path)
        _create_init(version_path)
        _create_base(version_path)


def location(version):
    return "cimpy." + version + ".Base"


base = {"base_class": "Base", "class_location": location}

template_files = [{"filename": "cimpy_class_template.mustache", "ext": ".py"}]


def get_class_location(class_name, class_map, version):
    # Check if the current class has a parent class
    if class_map[class_name].superClass():
        if class_map[class_name].superClass() in class_map:
            return "cimpy." + version + "." + class_map[class_name].superClass()
        elif class_map[class_name].superClass() == "Base" or class_map[class_name].superClass() is None:
            return location(version)
    else:
        return location(version)


partials = {}


# called by chevron, text contains the label {{dataType}}, which is evaluated by the renderer (see class template)
def _set_default(text, render):
    return _get_type_and_default(text, render)[1]


def _set_type(text, render):
    return _get_type_and_default(text, render)[0]


def _get_type_and_default(text, renderer) -> tuple[str, str]:
    result = renderer(text)
    # the field {{dataType}} either contains the multiplicity of an attribute if it is a reference or otherwise the
    # datatype of the attribute. If no datatype is set and there is also no multiplicity entry for an attribute, the
    # default value is set to None. The multiplicity is set for all attributes, but the datatype is only set for basic
    # data types. If the data type entry for an attribute is missing, the attribute contains a reference and therefore
    # the default value is either None or [] depending on the multiplicity. See also write_python_files
    # The default will be copied as-is, hence the possibility to have default or default_factory.
    if result in ["M:1", "M:0..1", "M:1..1", ""]:
        return ("Optional[str]", "default=None")
    elif result in ["M:0..n", "M:1..n"] or "M:" in result:
        return ("list", "default_factory=list")

    result = result.split("#")[1]
    if result in ["integer", "Integer", "Seconds"]:
        return ("int", "default=0")
    elif result in ["String", "DateTime", "Date"]:
        return ("str", 'default=""')
    elif result == "Boolean":
        return ("bool", "default=False")
    else:
        # everything else should be a float
        return ("float", "default=0.0")


def set_enum_classes(new_enum_classes):
    return


def set_float_classes(new_float_classes):
    return


def run_template(version_path, class_details):
    for template_info in template_files:
        class_file = os.path.join(version_path, class_details["class_name"] + template_info["ext"])
        if not os.path.exists(class_file):
            with open(class_file, "w", encoding="utf-8") as file:
                template_path = os.path.join(os.getcwd(), "modernpython/templates", template_info["filename"])
                class_details["setDefault"] = _set_default
                class_details["setType"] = _set_type
                with open(template_path, encoding="utf-8") as f:
                    args = {
                        "data": class_details,
                        "template": f,
                        "partials_dict": partials,
                    }
                    output = chevron.render(**args)
                file.write(output)


def _create_init(path):
    init_file = path + "/__init__.py"

    with open(init_file, "w", encoding="utf-8") as init:
        init.write("# pylint: disable=too-many-lines,missing-module-docstring\n")


# creates the Base class file, all classes inherit from this class
def _create_base(path):
    # TODO: Check export priority of OP en SC, see Profile class
    base_path = path + "/Base.py"
    with open(Path(__file__).parent / "Base.py", encoding="utf-8") as src, open(
        base_path, "w", encoding="utf-8"
    ) as dst:
        dst.write(src.read())


def resolve_headers(dest: str, version: str):
    """Add all classes in __init__.py"""
    if match := re.search(r"(?P<num>\d+_\d+_\d+)", version):  # NOSONAR
        version_number = match.group("num").replace("_", ".")
    else:
        raise ValueError(f"Cannot parse {version} to extract a number.")

    dest = Path(dest)
    with open(dest / "__init__.py", "a", encoding="utf-8") as header_file:
        _all = []
        for include_name in sorted(dest.glob("*.py")):
            stem = include_name.stem
            if stem == "__init__":
                continue
            _all.append(stem)
            header_file.write(f"from .{stem} import {stem}\n")

        header_file.write(f"CGMES_VERSION='{version_number}'\n")
        _all.append("CGMES_VERSION")

        header_file.write(
            "\n".join(
                [
                    "# This is not needed per se, but by referencing all imports",
                    "# this prevents a potential autoflake from cleaning up the whole file.",
                    "# FYA, if __all__ is present, only what's in there will be import with a import *",
                    "",
                ]
            )
        )
        header_file.write(f"__all__={_all}")
