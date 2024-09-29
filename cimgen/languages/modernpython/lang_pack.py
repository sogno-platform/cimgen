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
# cgmes_profile_details contains index, names und uris for each profile.
# We don't use that here because we aren't creating the header
# data for the separate profiles.
def setup(output_path: str, cgmes_profile_details: list, cim_namespace: str):  # NOSONAR
    for file in Path(output_path).glob("**/*.py"):
        file.unlink()

    # Add all hardcoded utils and create parent dir
    source_dir = Path(__file__).parent / "utils"
    dest_dir = Path(output_path) / "utils"

    copy_tree(str(source_dir), str(dest_dir))


def location(version):
    return "..utils.base"


base = {"base_class": "Base", "class_location": location}

# These are the files that are used to generate the python files.
template_files = [{"filename": "cimpy_class_template.mustache", "ext": ".py"}]


def get_class_location(class_name, class_map, version):
    return f".{class_map[class_name].superClass()}"


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
    if result in ["integer", "Integer"]:
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


def run_template(output_path, class_details):
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

            with open(resource_file, "w", encoding="utf-8") as file:
                class_details["setDefault"] = _set_default
                class_details["setType"] = _set_type

                templates = files("cimgen.languages.modernpython.templates")
                with templates.joinpath(template_info["filename"]).open(encoding="utf-8") as f:
                    args = {
                        "data": class_details,
                        "template": f,
                        "partials_dict": partials,
                    }
                    output = chevron.render(**args)
                file.write(output)


def resolve_headers(dest: str, version: str):
    """Add all classes in __init__.py"""

    if match := re.search(r"(?P<num>\d+_\d+_\d+)", version):  # NOSONAR
        version_number = match.group("num").replace("_", ".")
    else:
        raise ValueError(f"Cannot parse {version} to extract a number.")

    dest = Path(dest) / "resources"
    with open(dest / "__init__.py", "a", encoding="utf-8") as header_file:
        header_file.write(f"CGMES_VERSION='{version_number}'\n")

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
