import chevron
import shutil
from pathlib import Path
from importlib.resources import files
from typing import Callable


# Setup called only once: make output directory, create base class, create profile class, etc.
# This just makes sure we have somewhere to write the classes.
# cgmes_profile_details contains index, names and uris for each profile.
# We use that to create the header data for the profiles.
def setup(output_path: str, cgmes_profile_details: list[dict], namespaces: dict[str, str]) -> None:
    source_dir = Path(__file__).parent
    dest_dir = Path(output_path)
    for file in dest_dir.glob("**/*.[ch]*"):
        file.unlink()
    # Add all hardcoded utils and create parent dir
    for file in source_dir.glob("static/*.[ch]*"):
        dest_file = dest_dir / file.relative_to(source_dir)
        dest_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(file, dest_file)
    _create_cgmes_profile(dest_dir, cgmes_profile_details, namespaces["cim"])


# These are the files that are used to generate the header and object files.
# There is a template set for the large number of classes that are floats. They
# have unit, multiplier and value attributes in the schema, but only appear in
# the file as a float string.
template_files = [
    {"filename": "cpp_header_template.mustache", "ext": ".hpp"},
    {"filename": "cpp_object_template.mustache", "ext": ".cpp"},
]
float_template_files = [
    {"filename": "cpp_float_header_template.mustache", "ext": ".hpp"},
    {"filename": "cpp_float_object_template.mustache", "ext": ".cpp"},
]
enum_template_files = [
    {"filename": "cpp_enum_header_template.mustache", "ext": ".hpp"},
    {"filename": "cpp_enum_object_template.mustache", "ext": ".cpp"},
]
string_template_files = [
    {"filename": "cpp_string_header_template.mustache", "ext": ".hpp"},
    {"filename": "cpp_string_object_template.mustache", "ext": ".cpp"},
]
profile_template_files = [
    {"filename": "cpp_profile_header_template.mustache", "ext": ".hpp"},
    {"filename": "cpp_profile_object_template.mustache", "ext": ".cpp"},
]
classlist_template = {"filename": "cpp_classlist_template.mustache", "ext": ".hpp"}
iec61970_template = {"filename": "cpp_iec61970_template.mustache", "ext": ".hpp"}

partials = {
    "label_without_keyword": "{{#lang_pack.label_without_keyword}}{{label}}{{/lang_pack.label_without_keyword}}",
    "set_default": "{{#lang_pack.set_default}}{{datatype}}{{/lang_pack.set_default}}",
}


def get_base_class() -> str:
    return "BaseClass"


def get_class_location(class_name: str, class_map: dict, version: str) -> str:  # NOSONAR
    return ""


# This is the function that runs the template.
def run_template(output_path: str, class_details: dict) -> None:

    # Add some class infos
    class_details["attribute_class_includes"] = _get_attribute_class_includes(class_details["attributes"])
    class_details["attribute_class_declarations"] = _get_attribute_class_declarations(class_details["attributes"])
    class_details["nullptr_assigns"] = _get_nullptr_assigns(class_details["attributes"])

    # Add some attribute infos
    for attribute in class_details["attributes"]:
        attribute["attribute_is_primitive_string"] = _attribute_is_primitive_string(attribute) and "true" or ""
        if "inverse_role" in attribute:
            attribute["inverse_role"] = [attribute["inverse_role"].replace(".", "_")]
        else:
            attribute["inverse_role"] = []

    if class_details["is_a_datatype_class"] or class_details["class_name"] in ("Float", "Decimal"):
        templates = float_template_files
    elif class_details["is_an_enum_class"]:
        templates = enum_template_files
    elif class_details["is_a_primitive_class"]:
        templates = string_template_files
    else:
        templates = template_files

    if class_details["class_name"] in ("Integer", "Boolean"):
        # These classes are defined already
        # We have to implement operators for them
        return

    for template_info in templates:
        class_file = Path(output_path) / (class_details["class_name"] + template_info["ext"])
        _write_templated_file(class_file, class_details, template_info["filename"])


def _write_templated_file(class_file: Path, class_details: dict, template_filename: str) -> None:
    with class_file.open("w", encoding="utf-8") as file:
        templates = files("cimgen.languages.cpp.templates")
        with templates.joinpath(template_filename).open(encoding="utf-8") as f:
            args = {
                "data": class_details,
                "template": f,
                "partials_dict": partials,
            }
            output = chevron.render(**args)
        file.write(output)


def _create_cgmes_profile(output_path: Path, profile_details: list[dict], cim_namespace: str) -> None:
    for template_info in profile_template_files:
        class_file = output_path / ("CGMESProfile" + template_info["ext"])
        class_details = {
            "profiles": profile_details,
            "cim_namespace": cim_namespace,
        }
        _write_templated_file(class_file, class_details, template_info["filename"])


# This function just allows us to avoid declaring a variable called 'switch',
# which is in the definition of the ExcBBC class.
def label_without_keyword(text: str, render: Callable[[str], str]) -> str:
    label = render(text)
    return _get_label_without_keyword(label)


def _get_label_without_keyword(label: str) -> str:
    if label == "switch":
        return "_switch"
    return label


def _get_nullptr_assigns(attributes: list[dict]) -> str:
    # nullptr_list = [attr["label"] + "(nullptr)" for attr in attributes if attr["is_class_attribute"]]
    nullptr_list = []
    for attribute in attributes:
        if attribute["is_class_attribute"]:
            nullptr_list.append(attribute["label"] + "(nullptr)")
    if nullptr_list:
        return " : " + ", ".join(nullptr_list)
    return ""


def _get_attribute_class_includes(attributes: list[dict]) -> list[str]:
    class_set = set()
    for attribute in attributes:
        if _attribute_is_primitive_or_datatype_or_enum(attribute):
            class_set.add(attribute["attribute_class"])
    return list(sorted(class_set))


def _get_attribute_class_declarations(attributes: list[dict]) -> list[str]:
    class_set = set()
    for attribute in attributes:
        if not _attribute_is_primitive_or_datatype_or_enum(attribute):
            class_set.add(attribute["attribute_class"])
    return list(sorted(class_set))


def set_default(text: str, render: Callable[[str], str]) -> str:
    result = render(text)
    return _set_default(result)


def _set_default(datatype: str) -> str:
    # the field {{datatype}} either contains the multiplicity of an attribute if it is a reference or otherwise the
    # datatype of the attribute. If no datatype is set and there is also no multiplicity entry for an attribute, the
    # default value is set to None. The multiplicity is set for all attributes, but the datatype is only set for basic
    # data types. If the data type entry for an attribute is missing, the attribute contains a reference and therefore
    # the default value is either None or [] depending on the multiplicity. See also _write_files in cimgen.py.
    if datatype in ["M:1", "M:0..1", "M:1..1", "M:0..n", "M:1..n", ""] or "M:" in datatype:
        return "0"
    datatype = datatype.split("#")[1]
    if datatype in ["integer", "Integer"]:
        return "0"
    elif datatype in ["String", "DateTime", "Date"]:
        return "''"
    elif datatype == "Boolean":
        return "false"
    elif datatype == "Float":
        return "0.0"
    else:
        return "nullptr"


def _attribute_is_primitive_or_datatype_or_enum(attribute: dict) -> bool:
    return attribute["is_primitive_attribute"] or attribute["is_datatype_attribute"] or attribute["is_enum_attribute"]


def _attribute_is_primitive_string(attribute: dict) -> bool:
    return attribute["is_primitive_attribute"] and (
        attribute["attribute_class"] not in ("Float", "Decimal", "Integer", "Boolean")
    )


# The code below this line is used after the main cim_generate phase to generate
# two include files. They are called CIMClassList.hpp and IEC61970.hpp, and
# contain the list of the class files and the list of define functions that add
# the generated functions into the function tables.

class_blacklist = [
    "assignments",
    "BaseClass",
    "BaseClassDefiner",
    "CGMESProfile",
    "CIMClassList",
    "CIMFactory",
    "CIMNamespaces",
    "Factory",
    "Folders",
    "IEC61970",
    "Task",
    "UnknownType",
]

iec61970_blacklist = ["CIMClassList", "CIMNamespaces", "Folders", "Task", "IEC61970"]


def _is_primitive_or_enum_class(file: Path) -> bool:
    with file.open(encoding="utf-8") as f:
        try:
            for line in f:
                if "static const BaseClassDefiner declare();" in line:
                    return False
        except UnicodeDecodeError as error:
            print("Warning: UnicodeDecodeError parsing {0}: {1}".format(file.name, error))
    return True


def _create_header_include_file(
    directory: Path, header_include_filename: str, template_info: dict[str, str], blacklist: list[str]
) -> None:
    classes = []
    for file in sorted(directory.glob("*.hpp"), key=lambda f: f.stem):
        class_name = file.stem
        if not _is_primitive_or_enum_class(file) and class_name not in blacklist:
            classes.append(class_name)
    path = directory / (header_include_filename + template_info["ext"])
    _write_templated_file(path, {"classes": classes}, template_info["filename"])


def resolve_headers(path: str, version: str) -> None:  # NOSONAR
    _create_header_include_file(
        Path(path),
        "CIMClassList",
        classlist_template,
        class_blacklist,
    )
    _create_header_include_file(
        Path(path),
        "IEC61970",
        iec61970_template,
        iec61970_blacklist,
    )
