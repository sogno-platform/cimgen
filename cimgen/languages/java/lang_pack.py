import chevron
import logging
import shutil
from pathlib import Path
from importlib.resources import files

logger = logging.getLogger(__name__)


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
class_template_file = {"filename": "java_class.mustache", "ext": ".java"}
enum_template_file = {"filename": "java_enum.mustache", "ext": ".java"}
constants_template_file = {"filename": "java_constants.mustache", "ext": ".java"}
profile_template_file = {"filename": "java_profile.mustache", "ext": ".java"}
classlist_template_file = {"filename": "java_classlist.mustache", "ext": ".java"}


def get_base_class() -> str:
    return "BaseClass"


def get_class_location(class_name: str, class_map: dict, version: str) -> str:  # NOSONAR
    return ""


# This is the function that runs the template.
def run_template(output_path: str, class_details: dict) -> None:

    # Add some attribute infos
    for attribute in class_details["attributes"]:
        attribute["is_primitive_string"] = "true" if _attribute_is_primitive_string(attribute) else ""
        if attribute["is_primitive_attribute"]:
            if _attribute_is_primitive_string(attribute):
                attribute["primitive_java_type"] = "String"
            elif attribute["attribute_class"] == "Decimal":
                attribute["primitive_java_type"] = "Float"
            else:
                attribute["primitive_java_type"] = attribute["attribute_class"]
        attribute["variable_name"] = _variable_name(attribute["label"], class_details["class_name"])
        attribute["getter_name"] = _getter_setter_name("get", attribute["label"])
        attribute["setter_name"] = _getter_setter_name("set", attribute["label"])
        if attribute["is_class_attribute"] or attribute["is_list_attribute"]:
            if "inverse_role" in attribute:
                inverse_label = attribute["inverse_role"].split(".")[1]
                attribute["inverse_setter"] = [_getter_setter_name("set", inverse_label)]
            else:
                attribute["inverse_setter"] = []

    if class_details["is_a_primitive_class"] or class_details["is_a_datatype_class"]:
        return
    if class_details["is_an_enum_class"]:
        template = enum_template_file
        class_category = "types"
    else:
        template = class_template_file
        class_category = ""
    class_file = Path(output_path) / class_category / (class_details["class_name"] + template["ext"])
    _write_templated_file(class_file, class_details, template["filename"])


def _write_templated_file(class_file: Path, class_details: dict, template_filename: str) -> None:
    class_file.parent.mkdir(parents=True, exist_ok=True)
    with class_file.open("w", encoding="utf-8") as file:
        templates = files("cimgen.languages.java.templates")
        with templates.joinpath(template_filename).open(encoding="utf-8") as f:
            args = {
                "data": class_details,
                "template": f,
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


def _variable_name(label: str, class_name: str) -> str:
    """Get the name of the label used as variable name.

    Some label names are not allowed as name of a variable.
    Prevent collision of label and class_name (e.g. AvailabilitySchedule in profile AvailabilitySchedule).

    :param label:       Original label
    :param class_name:  Original class name
    :return:            Variable name
    """
    if label == "switch" or label == class_name:
        label += "_"
    return label


def _getter_setter_name(prefix: str, label: str) -> str:
    """Get the name of the getter/setter function for a label.

    Add "get"/"set" as prefix and change the first character of the label to upper case.
    Prevent collision of "Name" with "name" in IdentifiedObject, NameType, NamingAuthority.

    :param prefix:  "get"/"set"
    :param label:   Original label
    :return:        Name of the getter/setter function
    """
    if label[0].islower():
        label = label[0].upper() + label[1:]
    elif label == "Name":
        label = "_" + label
    return prefix + label


def _attribute_is_primitive_string(attribute: dict) -> bool:
    """Check if the attribute is a primitive attribute that is used like a string (Date, MonthDay etc).

    :param attribute: Dictionary with information about an attribute.
    :return:          Attribute is a primitive string?
    """
    return attribute["is_primitive_attribute"] and (
        attribute["attribute_class"] not in ("Float", "Decimal", "Integer", "Boolean")
    )


# The code below this line is used after the main cim_generate phase to generate CimClassMap.java.

class_blacklist = [
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
