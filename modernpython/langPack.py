import logging
import os
import re
from distutils.dir_util import copy_tree
import shutil
import sys
import textwrap
from pathlib import Path
import ast

import chevron

logger = logging.getLogger(__name__)


# This makes sure we have somewhere to write the classes, and
# creates a couple of files the python implementation needs.
# cgmes_profile_info details which uri belongs in each profile.
# We don't use that here because we aren't creating the header
# data for the separate profiles.
def setup(version_path, cgmes_profile_info):  # NOSONAR
    # version_path is actually the output_path

    # Add all hardcoded utils and create parent dir
    source_dir=Path(__file__).parent/"utils"
    dest_dir=Path(version_path)/"utils"

    copy_tree(str(source_dir), str(dest_dir))



def location(version):
    return "..utils.base"


base = {"base_class": "Base", "class_location": location}

template_files = [{"filename": "cimpy_class_template.mustache", "ext": ".py"}]
enum_template_files = [{"filename": "enum_class_template.mustache", "ext": ".py"}]
primitive_template_files = [{"filename": "primitive_template.mustache", "ext": ".py"}]
cimdatatype_template_files = [{"filename": "cimdatatype_template.mustache", "ext": ".py"}]

def get_class_location(class_name, class_map, version):
    return f".{class_map[class_name].superClass()}"
    # Check if the current class has a parent class

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

def _compute_cim_data_type(attributes) -> tuple[str, str, str]:
    python_type = 'None'
    unit = 'UnitSymbol.none'
    multiplier = 'UnitMultiplier.none'
    for attribute in attributes:
        if 'about' in attribute and attribute['about'] and "value" in attribute['about'] and 'class_name' in attribute:
            python_type = _primitive_to_data_type(attribute['class_name'])
        if 'about' in attribute and attribute['about'] and "multiplier" in attribute['about'] and 'isFixed' in attribute:
            multiplier = "UnitMultiplier."+attribute['isFixed']
        if 'about' in attribute and attribute['about'] and "unit" in attribute['about'] and 'isFixed' in attribute:
            unit = "UnitSymbol."+attribute['isFixed']
    return (python_type, unit, multiplier)


# set the cim datatype for a field
def _set_cim_data_type(text, render) -> str:
    attribute = eval(render(text))
    if is_primitive_class(attribute["class_name"]):
        return "data_type = " + attribute["class_name"] + ","
    elif is_primitive_class(attribute["class_name"]) or attribute["class_name"] == "String":
        return "data_type = String,"
    elif is_cim_data_type_class(attribute["class_name"]):
        return "data_type = " + attribute["class_name"] + ","
    return ""

# computes the data type
def _compute_data_type(attribute):
    if "label" in attribute and attribute["label"] == "mRID":
        return "str"
    elif "range" in attribute:
        return attribute["range"].split("#")[1]
    elif "dataType" in attribute and "class_name" in attribute:
        # for whatever weird reason String is not created as class from CIMgen
        if is_primitive_class(attribute["class_name"]) or attribute["class_name"] == "String":
            return _primitive_to_data_type(attribute["dataType"].split("#")[1])
        # the assumption is that cim data type e.g. Voltage, ActivePower, always
        # maps to a float
        elif is_cim_data_type_class(attribute["class_name"]):
            return "float"
        else:
        # this is for example the case for 'StreetAddress.streetDetail'
            return attribute["dataType"].split("#")[1]
    else:
        raise ValueError(f"Cannot parse {attribute} to extract a data type.")

def _ends_with_s(attribute_name):
    return attribute_name.endswith("s")

# called by chevron, text contains the label {{dataType}}, which is evaluated by the renderer (see class template)
def _set_default(text, render):
    return _get_type_and_default(text, render)[1]


def _set_type(text, render):
    return _get_type_and_default(text, render)[0]

def _lower_case_first_char(str):
    return str[:1].lower() + str[1:] if str else ""

# attributes should never have the same name as a class the may map to
# Python won't be happy with that, so let's normalize attribute names
# and leverage aliasing in pydantic to use the cim attribute capitalization
# during value setting.
def _set_normalized_name(text, render):
    return _lower_case_first_char(render(text))

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
    
# called by chevron, text contains the label {{dataType}}, which is evaluated by the renderer (see class template)
def _set_imports(text, render):
    rendered = render(text)
    res = None
    classes = set()
    try:
        res = eval(rendered)
    except Exception:
        pass
    if res:
        for val in res:
            if "range" in val:
                classes.add(val["range"].split("#")[1])
            elif not is_primitive_class(val["class_name"]) and val["class_name"] != "String" and not is_cim_data_type_class(val["class_name"]):
                classes.add(val["dataType"].split("#")[1])
    result = ""
    for val in classes:
        result += "from ." + val + " import " + val + "\n"
    return result

# called by chevron, text contains the label {{dataType}}, which is evaluated by the renderer (see class template)
def _set_validator(text, render):
    attribute = eval(render(text))

    if not is_primitive_class(attribute["class_name"]) and attribute["class_name"] != "String" and not is_cim_data_type_class(attribute["class_name"]):
        return (
            "val_"
            + _lower_case_first_char(attribute["label"])
            + '_wrap = field_validator("'
            + _lower_case_first_char(attribute["label"])
            + '", mode="wrap")(cyclic_references_validator)'
        )
    elif attribute["label"] == "mRID":
        return (
            '@field_validator("mRID", mode="before")\n'
            + "    def validate_mrid_format(cls, v):\n"
            + "      if isinstance(v, uuid.UUID):\n"
            + "        return str(v)\n"
            + "      elif isinstance(v, str):\n"
            + "        return v\n"
            + "      else:\n"
            + '        raise ValueError("must be a UUID or str")\n'
        )
    else:
        return ""

def _get_type_and_default(text, renderer) -> tuple[str, str]:
    # the field {{dataType}} either contains the multiplicity of an attribute if it is a reference or otherwise the
    # datatype of the attribute. If no datatype is set and there is also no multiplicity entry for an attribute, the
    # default value is set to None. The multiplicity is set for all attributes, but the datatype is only set for basic
    # data types. If the data type entry for an attribute is missing, the attribute contains a reference and therefore
    # the default value is either None or [] depending on the multiplicity. See also write_python_files
    # The default will be copied as-is, hence the possibility to have default or
    # default_factory.
    attribute = eval(renderer(text))
    datatype = _compute_data_type(attribute)
    field_type = datatype
    default = 'default=None'
    if "multiplicity" in attribute:
        multiplicity = attribute["multiplicity"]
        if multiplicity in ["M:0..1"]:
            field_type = "Optional[" + datatype + "]"
        elif multiplicity in ["M:0..n"]:
            field_type = "Optional[List[" + datatype + "]]"
        elif multiplicity in ["M:1..n", "M:2..n"]:
            field_type = "List[" + datatype + "]"
        elif multiplicity in ["M:1"] and attribute['label'] == 'PowerSystemResources':
            # Most probably there is a bug in the RDF that states multiplicity
            # M:1 but should be M:1..N
            field_type = "List[" + datatype + "]"
        else:
            field_type = datatype

    if "label" in attribute and attribute["label"] == "mRID":
        default = "default_factory=uuid.uuid4"
    elif "multiplicity" in attribute:
        multiplicity = attribute["multiplicity"]
        if multiplicity in ["M:1"] and attribute['label'] == 'PowerSystemResources':
            # Most probably there is a bug in the RDF that states multiplicity
            # M:1 but should be M:1..N
            default = 'default_factory=list'
        elif multiplicity in ["M:0..n"] or multiplicity in ["M:1..n"]:
            default = 'default_factory=list'
        elif field_type == 'int':
            default = 'default=0'
        elif field_type == 'str':
            default = 'default=""'
        elif field_type == 'float':
            default = 'default=0.0'
        elif field_type == 'bool':
            default = 'default=False'
    return (field_type, default)


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

def has_unit_attribute(attributes):
    for attr in attributes:
        if attr["label"] == "unit":
            return True
    return False

def run_template(version_path, class_details):
    if class_details["class_name"] == 'PositionPoint':
        #this class is created manually to support types conversions
        return
    elif class_details["is_a_primitive"] is True:
        # Primitives are never used in the in memory representation but only for
        # the schema
        run_template_primitive(version_path, class_details, primitive_template_files)
    elif class_details["is_a_cim_data_type"] is True:
        # Datatypes based on primitives are never used in the in memory
        # representation but only for the schema
        run_template_cimdatatype(version_path, class_details, cimdatatype_template_files)
    elif class_details["has_instances"] is True:
        run_template_enum(version_path, class_details, enum_template_files)
    else:
        run_template_schema(version_path, class_details, template_files)

def run_template_enum(version_path, class_details, templates):
    for template_info in templates:
        class_file = Path(version_path, "resources",  "enum" + template_info["ext"])
        if not os.path.exists(class_file):
            if not (parent:=class_file.parent).exists():
                parent.mkdir()
            with open(class_file, "w", encoding="utf-8") as file:
                header_file_path = os.path.join(
                    os.getcwd(), "modernpython", "enum_header.py"
                )
                header_file = open(header_file_path, "r")
                file.write(header_file.read())
        with open(class_file, "a", encoding="utf-8") as file:
            template_path = os.path.join(os.getcwd(), "modernpython/templates", template_info["filename"])
            class_details["setInstances"] = _set_instances
            with open(template_path, encoding="utf-8") as f:
                args = {
                    "data": class_details,
                    "template": f,
                    "partials_dict": partials,
                }
                output = chevron.render(**args)
            file.write(output)

def run_template_schema(version_path, class_details, templates):
    for template_info in templates:
        class_file =Path(version_path, "resources", "schema" + template_info["ext"])
        if not os.path.exists(class_file):
            if not (parent:=class_file.parent).exists():
                parent.mkdir()
            with open(class_file, "w", encoding="utf-8") as file:
                schema_file_path = os.path.join(
                    os.getcwd(), "modernpython", "schema_header.py"
                )
                schema_file = open(schema_file_path, "r")
                file.write(schema_file.read())
        with open(class_file, "a", encoding="utf-8") as file:
            template_path = os.path.join(os.getcwd(), "modernpython/templates", template_info["filename"])
            class_details["setDefault"] = _set_default
            class_details["setType"] = _set_type
            class_details["setImports"] = _set_imports
            class_details["setValidator"] = _set_validator
            class_details["setNormalizedName"] = _set_normalized_name
            class_details["setCimDataType"] = _set_cim_data_type
            with open(template_path, encoding="utf-8") as f:
                args = {
                    "data": class_details,
                    "template": f,
                    "partials_dict": partials,
                }
                output = chevron.render(**args)
            file.write(output)

def run_template_primitive(version_path, class_details, templates):
    for template_info in templates:
        class_file =Path(version_path, "resources", "primitive" + template_info["ext"])
        if not os.path.exists(class_file):
            if not (parent:=class_file.parent).exists():
                parent.mkdir()
            with open(class_file, "w", encoding="utf-8") as file:
                schema_file_path = os.path.join(
                    os.getcwd(), "modernpython", "primitive_header.py"
                )
                schema_file = open(schema_file_path, "r")
                file.write(schema_file.read())
        with open(class_file, "a", encoding="utf-8") as file:
            template_path = os.path.join(os.getcwd(), "modernpython/templates", template_info["filename"])
            class_details["data_type"] = _primitive_to_data_type(class_details["class_name"])
            with open(template_path, encoding="utf-8") as f:
                args = {
                    "data": class_details,
                    "template": f,
                    "partials_dict": partials,
                }
                output = chevron.render(**args)
            file.write(output)

def run_template_cimdatatype(version_path, class_details, templates):
    for template_info in templates:
        class_file =Path(version_path, "resources", "cimdatatype" + template_info["ext"])
        if not os.path.exists(class_file):
            if not (parent:=class_file.parent).exists():
                parent.mkdir()
            with open(class_file, "w", encoding="utf-8") as file:
                schema_file_path = os.path.join(
                    os.getcwd(), "modernpython", "cimdatatype_header.py"
                )
                schema_file = open(schema_file_path, "r")
                file.write(schema_file.read())
        with open(class_file, "a", encoding="utf-8") as file:
            template_path = os.path.join(os.getcwd(), "modernpython/templates", template_info["filename"])
            class_details["data_type"] = _compute_cim_data_type(class_details["attributes"])[0]
            class_details["unit"] = _compute_cim_data_type(class_details["attributes"])[1]
            class_details["multiplier"] = _compute_cim_data_type(class_details["attributes"])[2]
            with open(template_path, encoding="utf-8") as f:
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

    dest = Path(dest)/"resources"
    with open(dest / "__init__.py", "a", encoding="utf-8") as header_file:
        header_file.write("# pylint: disable=too-many-lines,missing-module-docstring\n")
        header_file.write(f"CGMES_VERSION='{version_number}'\n")
