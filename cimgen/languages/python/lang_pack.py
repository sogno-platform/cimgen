import os
import chevron
import logging
import glob
from importlib.resources import files
from typing import Callable

logger = logging.getLogger(__name__)


# Setup called only once: make output directory, create base class, create profile class, etc.
# This makes sure we have somewhere to write the classes, and
# creates a couple of files the python implementation needs.
# cgmes_profile_details contains index, names and uris for each profile.
# We use that to create the header data for the profiles.
def setup(output_path: str, cgmes_profile_details: list[dict], namespaces: dict[str, str]) -> None:
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    else:
        for filename in os.listdir(output_path):
            os.remove(os.path.join(output_path, filename))
    _create_base(output_path)
    _create_cgmes_profile(output_path, cgmes_profile_details, namespaces["cim"])


# These are the files that are used to generate the python files.
class_template_file = {"filename": "cimpy_class_template.mustache", "ext": ".py"}
profile_template_file = {"filename": "cimpy_profile_template.mustache", "ext": ".py"}

partials = {}


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
        return '"list"'

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


def get_base_class() -> str:
    return "Base"


def get_class_location(class_name: str, class_map: dict, version: str) -> str:
    # Check if the current class has a parent class
    if class_map[class_name].subclass_of() and class_map[class_name].subclass_of() in class_map:
        return "cimpy." + version + "." + class_map[class_name].subclass_of()
    return "cimpy." + version + ".Base"


def run_template(output_path: str, class_details: dict) -> None:
    if class_details["class_name"] == "String":
        return
    class_file = os.path.join(output_path, class_details["class_name"] + class_template_file["ext"])
    _write_templated_file(class_file, class_details, class_template_file["filename"])


def _write_templated_file(class_file: str, class_details: dict, template_filename: str) -> None:
    with open(class_file, "w", encoding="utf-8") as file:
        class_details["set_default"] = _set_default
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
def _create_base(path: str) -> None:
    base_path = path + "/Base.py"
    base = [
        "class Base:\n",
        '    """\n',
        "    Base Class for CIM\n",
        '    """\n\n',
        "    def printxml(self, dict={}):\n",
        "        return dict\n",
    ]
    with open(base_path, "w", encoding="utf-8") as f:
        for line in base:
            f.write(line)


def _create_cgmes_profile(output_path: str, profile_details: list[dict], cim_namespace: str) -> None:
    class_file = os.path.join(output_path, "CGMESProfile" + profile_template_file["ext"])
    class_details = {
        "profiles": profile_details,
        "cim_namespace": cim_namespace,
    }
    _write_templated_file(class_file, class_details, profile_template_file["filename"])


class_blacklist = ["CGMESProfile"]


def resolve_headers(path: str, version: str) -> None:  # NOSONAR
    """Add all classes in __init__.py"""
    filenames = glob.glob(path + "/*.py")
    include_names = []
    for filename in sorted(filenames):
        include_names.append(os.path.splitext(os.path.basename(filename))[0])
    with open(path + "/__init__.py", "w", encoding="utf-8") as header_file:
        for include_name in include_names:
            if include_name not in class_blacklist:
                header_file.write(
                    "from " + "." + include_name + " import " + include_name + " as " + include_name + "\n"
                )
        header_file.close()
