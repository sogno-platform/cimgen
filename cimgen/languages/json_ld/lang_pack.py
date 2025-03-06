from importlib.resources import files
import os
from typing import Callable
import chevron
import logging

logger = logging.getLogger(__name__)


# This makes sure we have somewhere to write the generated files
def setup(output_path: str, cgmes_profile_details: list[dict], cim_namespace: str) -> None:
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    else:
        for filename in os.listdir(output_path):
            os.remove(os.path.join(output_path, filename))


def get_base_class() -> str:
    return "Base"


# called by chevron, text contains the label {{datatype}}, which is evaluated by the renderer (see class template)
def _set_default(text: str, render: Callable[[str], str]) -> str:
    result = render(text)

    # the field {{datatype}} either contains the multiplicity of an attribute if it is a reference or otherwise the
    # datatype of the attribute. If no datatype is set and there is also no multiplicity entry for an attribute, the
    # default value is set to None. The multiplicity is set for all attributes, but the datatype is only set for basic
    # data types. If the data type entry for an attribute is missing, the attribute contains a reference and therefore
    # the default value is either None or [] depending on the multiplicity. See also write_python_files
    if result in ["M:1", "M:0..1", "M:1..1", ""]:
        return "None"
    elif result in ["M:0..n", "M:1..n"] or "M:" in result:
        return "[]"

    result = result.split("#")[1]
    if result in ["integer", "Integer"]:
        return "0"
    elif result in ["String", "DateTime", "Date"]:
        return "''"
    elif result == "Boolean":
        return "False"
    else:
        # everything else should be a float
        return "0.0"


# These are the template files that are used to generate the class files.
class_template_file = {"filename": "json_ld_template.mustache", "ext": ".json"}


def run_template(output_path: str, class_details: dict) -> None:
    class_file = os.path.join(output_path, class_details["class_name"] + class_template_file["ext"])
    with open(class_file, "w") as file:
        class_details["set_default"] = _set_default
        templates = files("cimgen.languages.json_ld.templates")
        with templates.joinpath(class_template_file["filename"]).open(encoding="utf-8") as f:
            args = {
                "data": class_details,
                "template": f,
            }
            output = chevron.render(**args)
            file.write(output)


def location(version):
    return "cimpy." + version + ".Base"


base = {"base_class": "Base", "class_location": location}

template_files = [{"filename": "json_ld_template.mustache", "ext": ".json"}]


def get_class_location(class_name, class_map, version):
    pass


def set_enum_classes(new_enum_classes):
    return


def set_float_classes(new_float_classes):
    return


def resolve_headers(path: str, version: str) -> None:  # NOSONAR
    pass
