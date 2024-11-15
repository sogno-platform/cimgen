import logging
import os
import re
from distutils.dir_util import copy_tree
from pathlib import Path
from importlib.resources import files

import chevron

logger = logging.getLogger(__name__)


# Setup called only once: make output directory, create base class, create profile class, etc.
# This makes sure we have somewhere to write the classes, and
# creates a couple of files the python implementation needs.
# cgmes_profile_details contains index, names and uris for each profile.
# We use that to create the header data for the profiles.
def setup(output_path: str, cgmes_profile_details: list, cim_namespace: str):
    for file in Path(output_path).glob("**/*.py"):
        file.unlink()

    # Add all hardcoded utils and create parent dir
    source_dir = Path(__file__).parent / "utils"
    dest_dir = Path(output_path) / "utils"

    copy_tree(str(source_dir), str(dest_dir))
    _create_constants(output_path, cim_namespace)
    _create_cgmes_profile(output_path, cgmes_profile_details)


def location(version):  # NOSONAR
    return "..utils.base"


base = {"base_class": "Base", "class_location": location}

# These are the files that are used to generate the python files.
template_files = [{"filename": "cimpy_class_template.mustache", "ext": ".py"}]
constants_template_files = [{"filename": "cimpy_constants_template.mustache", "ext": ".py"}]
profile_template_files = [{"filename": "cimpy_cgmesProfile_template.mustache", "ext": ".py"}]


def get_class_location(class_name, class_map, version):  # NOSONAR
    return f".{class_map[class_name].superClass()}"


partials = {}


# called by chevron, text contains the attribute infos, which are evaluated by the renderer (see class template)
def _set_default(text, render):
    return _get_type_and_default(text, render)[1]


def _set_type(text, render):
    return _get_type_and_default(text, render)[0]


def _get_type_and_default(text, render) -> tuple[str, str]:
    attribute_txt = render(text)
    attribute_json = eval(attribute_txt)
    if attribute_json["is_class_attribute"]:
        return ("Optional[str]", "default=None")
    elif attribute_json["is_list_attribute"]:
        return ("list", "default_factory=list")
    elif attribute_json["is_datatype_attribute"]:
        return ("float", "default=0.0")
    elif attribute_json["attribute_class"] in ("Float", "Decimal"):
        return ("float", "default=0.0")
    elif attribute_json["attribute_class"] == "Integer":
        return ("int", "default=0")
    elif attribute_json["attribute_class"] == "Boolean":
        return ("bool", "default=False")
    else:
        # everything else should be a string
        return ("str", 'default=""')


def run_template(output_path, class_details):
    if class_details["is_a_primitive_class"] or class_details["is_a_datatype_class"]:
        return
    for template_info in template_files:
        resource_file = Path(
            os.path.join(
                output_path,
                "resources",
                class_details["class_name"] + template_info["ext"],
            )
        )
        if not resource_file.exists():
            if not (parent := resource_file.parent).exists():
                parent.mkdir()
        class_details["setDefault"] = _set_default
        class_details["setType"] = _set_type
        _write_templated_file(resource_file, class_details, template_info["filename"])


def _write_templated_file(class_file, class_details, template_filename):
    with open(class_file, "w", encoding="utf-8") as file:
        templates = files("cimgen.languages.modernpython.templates")
        with templates.joinpath(template_filename).open(encoding="utf-8") as f:
            args = {
                "data": class_details,
                "template": f,
                "partials_dict": partials,
            }
            output = chevron.render(**args)
        file.write(output)


def _create_constants(output_path: str, cim_namespace: str):
    for template_info in constants_template_files:
        class_file = os.path.join(output_path, "utils", "constants" + template_info["ext"])
        class_details = {"cim_namespace": cim_namespace}
        _write_templated_file(class_file, class_details, template_info["filename"])


def _create_cgmes_profile(output_path: str, profile_details: list):
    for template_info in profile_template_files:
        class_file = os.path.join(output_path, "utils", "profile" + template_info["ext"])
        class_details = {"profiles": profile_details}
        _write_templated_file(class_file, class_details, template_info["filename"])


def resolve_headers(path: str, version: str):
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
