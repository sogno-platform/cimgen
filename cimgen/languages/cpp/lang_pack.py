import chevron
import shutil
from pathlib import Path
from importlib.resources import files


# Setup called only once: make output directory, create base class, create profile class, etc.
# This just makes sure we have somewhere to write the classes.
# cgmes_profile_details contains index, names and uris for each profile.
# We use that to create the header data for the profiles.
def setup(output_path: str, version: str, cgmes_profile_details: list[dict], namespaces: dict[str, str]) -> None:
    source_dir = Path(__file__).parent
    dest_dir = Path(output_path)
    for file in dest_dir.glob("**/*.[ch]*"):
        file.unlink()
    # Add all hardcoded utils and create parent dir
    for file in source_dir.glob("static/*.[ch]*"):
        dest_file = dest_dir / file.relative_to(source_dir)
        dest_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(file, dest_file)
    _create_constants(dest_dir, version, namespaces)
    _create_cgmes_profile(dest_dir, cgmes_profile_details)


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
constants_template_files = [
    {"filename": "cpp_constants_header_template.mustache", "ext": ".hpp"},
    {"filename": "cpp_constants_object_template.mustache", "ext": ".cpp"},
]
profile_template_files = [
    {"filename": "cpp_profile_header_template.mustache", "ext": ".hpp"},
    {"filename": "cpp_profile_object_template.mustache", "ext": ".cpp"},
]
classlist_template = {"filename": "cpp_classlist_template.mustache", "ext": ".hpp"}
iec61970_template = {"filename": "cpp_iec61970_template.mustache", "ext": ".hpp"}

partials = {}


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
        attribute["is_primitive_string"] = _attribute_is_primitive_string(attribute) and "true" or ""
        if "inverse_role" in attribute:
            attribute["inverse_role_name"] = attribute["inverse_role"].replace(".", "_")
        attribute["variable_name"] = _variable_name(attribute["label"], class_details["class_name"])
        attribute["default_value"] = _default_value(attribute)

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


def _create_constants(output_path: Path, version: str, namespaces: dict[str, str]) -> None:
    for template_info in constants_template_files:
        class_file = output_path / ("CimConstants" + template_info["ext"])
        namespaces_list = [{"ns": ns, "uri": uri} for ns, uri in sorted(namespaces.items())]
        class_details = {"version": version, "namespaces": namespaces_list}
        _write_templated_file(class_file, class_details, template_info["filename"])


def _create_cgmes_profile(output_path: Path, profile_details: list[dict]) -> None:
    for template_info in profile_template_files:
        class_file = output_path / ("CGMESProfile" + template_info["ext"])
        class_details = {"profiles": profile_details}
        _write_templated_file(class_file, class_details, template_info["filename"])


def _variable_name(label: str, class_name: str) -> str:
    """Get the name of the label used as variable name.

    Some label names are not allowed as name of a variable.
    Prevent collision of label and class_name (e.g. AvailabilitySchedule in profile AvailabilitySchedule).

    :param label:       Original label
    :param class_name:  Original class name
    :return:            Variable name
    """
    if label == "switch" or label == class_name:
        label = "_" + label
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


def _default_value(attribute: dict) -> str:
    """Get the default value of the attribute.

    :param attribute:  Dictionary with information about an attribute of a class.
    :return:           Default value
    """
    if attribute["is_datatype_attribute"]:
        return "0.0"
    if attribute["is_enum_attribute"]:
        return "0"
    if attribute["is_class_attribute"]:
        return "nullptr"
    if attribute["is_list_attribute"]:
        return "{}"
    # primitive attribute
    if attribute["attribute_class"] == "Integer":
        return "0"
    if attribute["attribute_class"] == "Boolean":
        return "false"
    if attribute["attribute_class"] in ("Float", "Decimal"):
        return "0.0"
    # primitive string attribute
    return '""'


def _attribute_is_primitive_or_datatype_or_enum(attribute: dict) -> bool:
    return attribute["is_primitive_attribute"] or attribute["is_datatype_attribute"] or attribute["is_enum_attribute"]


def _attribute_is_primitive_string(attribute: dict) -> bool:
    """Check if the attribute is a primitive attribute that is used like a string (Date, MonthDay etc).

    :param attribute: Dictionary with information about an attribute.
    :return:          Attribute is a primitive string?
    """
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
    "CimConstants",
    "Factory",
    "Folders",
    "IEC61970",
    "Task",
    "UnknownType",
]

iec61970_blacklist = ["CIMClassList", "CIMNamespaces", "CimConstants", "Folders", "Task", "IEC61970"]


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
