import os
import chevron
import json
from importlib.resources import files


def location(version):  # NOSONAR
    return ""


# Setup called only once: make output directory, create base class, create profile class, etc.
# This just makes sure we have somewhere to write the classes.
# cgmes_profile_details contains index, names and uris for each profile.
# We don't use that here because we aren't exporting into
# separate profiles.
def setup(output_path: str, cgmes_profile_details: list, cim_namespace: str):  # NOSONAR
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    else:
        for filename in os.listdir(output_path):
            os.remove(os.path.join(output_path, filename))


base = {"base_class": "BaseClass", "class_location": location}

# These are the files that are used to generate the java files.
# There is a template set for the large number of classes that are floats. They
# have unit, multiplier and value attributes in the schema, but only appear in
# the file as a float string.
template_files = [{"filename": "java_class.mustache", "ext": ".java"}]
float_template_files = [{"filename": "java_float.mustache", "ext": ".java"}]
enum_template_files = [{"filename": "java_enum.mustache", "ext": ".java"}]
string_template_files = [{"filename": "java_string.mustache", "ext": ".java"}]


def get_class_location(class_name, class_map, version):  # NOSONAR
    return ""


partials = {
    "attribute": "{{#langPack.attribute_decl}}{{.}}{{/langPack.attribute_decl}}",
    "label": "{{#langPack.label}}{{label}}{{/langPack.label}}",
}


# This is the function that runs the template.
def run_template(output_path, class_details):

    class_details["primitives"] = []
    for attr in class_details["attributes"]:
        if _attribute_is_primitive_or_datatype_or_enum(attr):
            class_details["primitives"].append(attr)

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
        class_file = os.path.join(output_path, class_details["class_name"] + template_info["ext"])
        _write_templated_file(class_file, class_details, template_info["filename"])


def _write_templated_file(class_file, class_details, template_filename):
    with open(class_file, "w", encoding="utf-8") as file:
        class_details["setDefault"] = _set_default
        templates = files("cimgen.languages.java.templates")
        with templates.joinpath(template_filename).open(encoding="utf-8") as f:
            args = {
                "data": class_details,
                "template": f,
                "partials_dict": partials,
            }
            output = chevron.render(**args)
        file.write(output)


# This function just allows us to avoid declaring a variable called 'switch',
# which is in the definition of the ExcBBC class.
def label(text, render):
    result = render(text)
    if result == "switch":
        return "_switch"
    else:
        return result


# These create_ functions are used to generate the implementations for
# the entries in the dynamic_switch maps referenced in assignments.cpp and Task.cpp
def create_class_assign(text, render):  # NOSONAR
    # TODO REMOVE:
    return ""


def create_assign(text, render):
    attribute_txt = render(text)
    attribute_json = eval(attribute_txt)
    assign = ""
    _class = attribute_json["attribute_class"]
    if not _attribute_is_primitive_or_datatype_or_enum(attribute_json):
        return ""
    label_without_keyword = attribute_json["label"]
    if label_without_keyword == "switch":
        label_without_keyword = "_switch"

    if _class != "String":
        assign = """
        public BaseClass assign_LABEL(String value) {
	    CLASS attr = new CLASS();
            attr.setValue(value);
            return attr;
        }
        """.replace(  # noqa: E101,W191
            "CLASS", _class
        ).replace(
            "LABEL", attribute_json["label"]
        )
    else:
        assign = """
        """.replace(
            "CLASS", attribute_json["domain"]
        ).replace(
            "LABEL", attribute_json["label"]
        )

    return assign


def attribute_decl(text, render):
    attribute_txt = render(text)
    attribute_json = eval(attribute_txt)
    return _attribute_decl(attribute_json)


def _attribute_decl(attribute):
    _class = attribute["attribute_class"]
    if _attribute_is_primitive_or_datatype_or_enum(attribute):
        return _class
    if attribute["is_list_attribute"]:
        return "List<" + _class + ">"
    else:
        return _class


def _create_attribute_includes(text, render):
    unique = {}
    include_string = ""
    inputText = render(text)
    jsonString = inputText.replace("'", '"')
    jsonStringNoHtmlEsc = jsonString.replace("&quot;", '"')
    if jsonStringNoHtmlEsc is not None and jsonStringNoHtmlEsc != "":
        attributes = json.loads(jsonStringNoHtmlEsc)
        for attribute in attributes:
            if _attribute_is_primitive_or_datatype_or_enum(attribute):
                unique[attribute["attribute_class"]] = True
    for clarse in unique:
        if clarse != "String":
            include_string += "\nimport cim4j." + clarse + ";"
    return include_string


def _create_attribute_class_declarations(text, render):
    unique = {}
    include_string = ""
    inputText = render(text)
    jsonString = inputText.replace("'", '"')
    jsonStringNoHtmlEsc = jsonString.replace("&quot;", '"')
    if jsonStringNoHtmlEsc is not None and jsonStringNoHtmlEsc != "":
        attributes = json.loads(jsonStringNoHtmlEsc)
        for attribute in attributes:
            if attribute["is_class_attribute"] or attribute["is_list_attribute"]:
                unique[attribute["attribute_class"]] = True
    for clarse in unique:
        include_string += "\nimport cim4j." + clarse + ";"
    return include_string


def _set_default(text, render):
    result = render(text)
    return set_default(result)


def set_default(dataType):

    # the field {{dataType}} either contains the multiplicity of an attribute if it is a reference or otherwise the
    # datatype of the attribute. If no datatype is set and there is also no multiplicity entry for an attribute, the
    # default value is set to None. The multiplicity is set for all attributes, but the datatype is only set for basic
    # data types. If the data type entry for an attribute is missing, the attribute contains a reference and therefore
    # the default value is either None or [] depending on the multiplicity. See also write_python_files
    if dataType in ["M:1", "M:0..1", "M:1..1", "M:0..n", "M:1..n", ""] or "M:" in dataType:
        return "0"
    dataType = dataType.split("#")[1]
    if dataType in ["integer", "Integer"]:
        return "0"
    elif dataType in ["String", "DateTime", "Date"]:
        return "''"
    elif dataType == "Boolean":
        return "false"
    else:
        return "nullptr"


def _attribute_is_primitive_or_datatype_or_enum(attribute: dict) -> bool:
    return attribute["is_primitive_attribute"] or attribute["is_datatype_attribute"] or attribute["is_enum_attribute"]


# The code below this line is used after the main cim_generate phase to generate
# two include files. They are called CIMClassList.hpp and IEC61970.hpp, and
# contain the list of the class files and the list of define functions that add
# the generated functions into the function tables.

class_blacklist = [
    "assignments",
    "AttributeInterface",
    "BaseClassInterface",
    "BaseClassBuilder",
    "PrimitiveBuilder",
    "BaseClass",
    "BaseClassDefiner",
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


def _is_enum_class(filepath):
    with open(filepath, encoding="utf-8") as f:
        try:
            for line in f:
                if "enum class" in line:
                    return True
        except UnicodeDecodeError as error:
            print("Warning: UnicodeDecodeError parsing {0}: {1}".format(filepath, error))
    return False


def _create_header_include_file(directory, header_include_filename, header, footer, before, after, blacklist):

    lines = []

    for filename in sorted(os.listdir(directory)):
        filepath = os.path.join(directory, filename)
        basepath, ext = os.path.splitext(filepath)
        basename = os.path.basename(basepath)
        if ext == ".java" and not _is_enum_class(filepath) and basename not in blacklist:
            lines.append(before + 'Map.entry("' + basename + '", new cim4j.' + basename + after + "),\n")
    lines[-1] = lines[-1].replace("),", ")")
    for line in lines:
        header.append(line)
    for line in footer:
        header.append(line)
    header_include_filepath = os.path.join(directory, header_include_filename)
    with open(header_include_filepath, "w", encoding="utf-8") as f:
        f.writelines(header)


def resolve_headers(path: str, version: str):  # NOSONAR
    class_list_header = [
        "/*\n",
        "Generated from the CGMES files via cimgen: https://github.com/sogno-platform/cimgen\n",
        "*/\n",
        "package cim4j;\n",
        "import java.util.Map;\n",
        "import java.util.Arrays;\n",
        "import static java.util.Map.entry;\n",
        "import cim4j.*;\n",
        "public class CIMClassMap {\n",
        "    public static boolean isCIMClass(java.lang.String key) {\n",
        "        return classMap.containsKey(key);\n",
        "    }\n",
        "    public static Map<java.lang.String, BaseClass> classMap = Map.ofEntries(\n",
    ]
    class_list_footer = ["    );\n", "}\n"]

    _create_header_include_file(
        path,
        "CIMClassMap.java",
        class_list_header,
        class_list_footer,
        "        ",
        "()",
        class_blacklist,
    )
