import logging
import os
import re
from distutils.dir_util import copy_tree
from pathlib import Path
from importlib.resources import files
import ast

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
enum_template_files = [{"filename": "enum_class_template.mustache", "ext": ".py"}]
primitive_template_files = [{"filename": "primitive_template.mustache", "ext": ".py"}]
cimdatatype_template_files = [{"filename": "cimdatatype_template.mustache", "ext": ".py"}]

def get_class_location(class_name, class_map, version):
    return f".{class_map[class_name].superClass()}"


partials = {}

def _primitive_to_data_type(datatype):
    if datatype.lower() == "integer":
        return "int"
    if datatype.lower() == "boolean":
        return "bool"
    if datatype.lower() == "string":
        return "str"
    if datatype.lower() == "datetime":
        return "datetime"
    if datatype.lower() == "monthday":
        return "str"  # TO BE FIXED? I could not find a datatype in python that holds only month and day.
    if datatype.lower() == "date":
        return "date"
    # as of today no CIM model is using only time.
    if datatype.lower() == "time":
        return "time"
    if datatype.lower() == "float":
        return "float"
    if datatype.lower() == "string":
        return "str"
    else:
    # this actually never happens
        return "float"
    
# called by chevron, text contains the label {{dataType}}, which is evaluated by the renderer (see class template)
def _set_default(text, render):
    return _get_type_and_default(text, render)[1]


def _set_type(text, render):
    return _get_type_and_default(text, render)[0]

# called by chevron, text contains the label {{dataType}}, which is evaluated by the renderer (see class template)
def _set_instances(text, render):
    instance = None
    try:
        # render(text) returns a python dict. Some fileds might be quoted by '&quot;' instead of '"', making the first evel fail.
        instance = ast.literal_eval(render(text))
    except SyntaxError as se:
        rendered = render(text)
        rendered = rendered.replace("&quot;", '"')
        instance = eval(rendered)
        logger.warning("Exception in evaluating %s : %s . Handled replacing quotes", rendered, se.msg)
    if "label" in instance:
        value = instance["label"] + ' = "' + instance["label"] + '"'
        if "comment" in instance:
            value += " #" + instance["comment"]
        return value
    else:
        return ""
    
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

primitive_classes = {}

def set_primitive_classes(new_primitive_classes):
    for new_class in new_primitive_classes:
        primitive_classes[new_class] = new_primitive_classes[new_class]

def is_primitive_class(name):
    if name in primitive_classes:
        return primitive_classes[name]
    
cim_data_type_classes = {}

def set_cim_data_type_classes(new_cim_data_type_classes):
    for new_class in new_cim_data_type_classes:
        cim_data_type_classes[new_class] = new_cim_data_type_classes[new_class]

def is_cim_data_type_class(name):
    if name in cim_data_type_classes:
        return cim_data_type_classes[name]

def run_template(output_path, class_details):
    # if class_details["class_name"] == 'PositionPoint':
    #     #this class is created manually to support types conversions
    #     return
    if class_details["is_a_primitive"] is True:
        # Primitives are never used in the in memory representation but only for
        # the schema
        run_template_primitive(output_path, class_details, primitive_template_files)
    # elif class_details["is_a_cim_data_type"] is True:
    #     # Datatypes based on primitives are never used in the in memory
    #     # representation but only for the schema
    #     run_template_cimdatatype(output_path, class_details, cimdatatype_template_files)
    elif class_details["has_instances"] is True:
        run_template_enum(output_path, class_details, enum_template_files)
    else:
        run_template_schema(output_path, class_details, template_files)

def run_template_schema(output_path, class_details, template_files):
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

def run_template_enum(output_path, class_details, template_files):
    for template_info in template_files:
        #class_file = Path(version_path, "resources",  "enum" + template_info["ext"])
        resource_file = Path(
            os.path.join(
                output_path,
                "resources","enum",
                class_details["class_name"] + template_info["ext"],
            )
        )
        if not os.path.exists(resource_file):
            if not (parent:=resource_file.parent).exists():
                parent.mkdir()
            # with open(class_file, "w", encoding="utf-8") as file:
            #     header_file_path = os.path.join(
            #         os.getcwd(), "modernpython", "enum_header.py"
            #     )
            #     header_file = open(header_file_path, "r")
            #     file.write(header_file.read())
        with open(resource_file, "a", encoding="utf-8") as file:
            class_details["setInstances"] = _set_instances

            templates = files("cimgen.languages.modernpython.templates")
            with templates.joinpath(template_info["filename"]).open(encoding="utf-8") as f:
                args = {
                    "data": class_details,
                    "template": f,
                    "partials_dict": partials,
                }
                output = chevron.render(**args)
            file.write(output)

def run_template_primitive(version_path, class_details, template_files):
    for template_info in template_files:
        resource_file =Path(version_path, "resources", "primitive",
                class_details["class_name"] + template_info["ext"])
        if not os.path.exists(resource_file):
            if not (parent:=resource_file.parent).exists():
                parent.mkdir()
            # with open(resource_file, "w", encoding="utf-8") as file:
            #     schema_file_path = os.path.join(
            #         os.getcwd(), "modernpython", "primitive_header.py"
            #     )
            #     schema_file = open(schema_file_path, "r")
            #     file.write(schema_file.read())
        with open(resource_file, "a", encoding="utf-8") as file:
            class_details["data_type"] = _primitive_to_data_type(class_details["class_name"])

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
