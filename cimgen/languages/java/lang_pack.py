import os
import chevron
import json
from importlib.resources import files


def location(version):
    return "BaseClass"


# This just makes sure we have somewhere to write the classes.
# cgmes_profile_info details which uri belongs in each profile.
# We don't use that here because we aren't exporting into
# separate profiles.
def setup(version_path, cgmes_profile_info):
    if not os.path.exists(version_path):
        os.makedirs(version_path)


base = {"base_class": "BaseClass", "class_location": location}

# These are the files that are used to generate the header and object files.
# There is a template set for the large number of classes that are floats. They
# have unit, multiplier and value attributes in the schema, but only appear in
# the file as a float string.
template_files = [{"filename": "java_class.mustache", "ext": ".java"}]
float_template_files = [{"filename": "java_float.mustache", "ext": ".java"}]
enum_template_files = [{"filename": "java_enum.mustache", "ext": ".java"}]


def get_class_location(class_name, class_map, version):
    pass


partials = {
    "attribute": "{{#langPack.attribute_decl}}{{.}}{{/langPack.attribute_decl}}",
    "label": "{{#langPack.label}}{{label}}{{/langPack.label}}",
    "insert_assign": "{{#langPack.insert_assign_fn}}{{.}}{{/langPack.insert_assign_fn}}",
    "insert_class_assign": "{{#langPack.insert_class_assign_fn}}{{.}}{{/langPack.insert_class_assign_fn}}",
}


# This is the function that runs the template.
def run_template(outputPath, class_details):

    class_details["primitives"] = []
    for attr in class_details["attributes"]:
        if attribute_type(attr) == "primitive":
            class_details["primitives"].append(attr)
    if class_details["is_a_float"]:
        templates = float_template_files
    elif class_details["has_instances"]:
        templates = enum_template_files
    else:
        templates = template_files

    if (
        class_details["class_name"] == "Integer"
        or class_details["class_name"] == "Boolean"
        or class_details["class_name"] == "Date"
    ):
        # These classes are defined already
        # We have to implement operators for them
        return

    for template_info in templates:
        class_file = os.path.join(outputPath, class_details["class_name"] + template_info["ext"])
        if not os.path.exists(class_file):
            with open(class_file, "w") as file:
                class_details["setDefault"] = _set_default
                templates = files("cimgen.languages.java.templates")
                with templates.joinpath(template_info["filename"]).open() as f:
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


# This function determines how the attribute code will be implemented.
#  - attributes which are primitives will be read from the file and
#    stored in the class object we are reading at the time
#  - attributes which are classes will be stored as pointers to the
#    actual class, which will be read from another part of the file.
#  - attributes with multiplicity of 1..n or 0..n will be std::lists
#    of pointers to classes read from a different part of the file
def attribute_type(attribute):
    class_name = attribute["class_name"]
    if attribute["multiplicity"] == "M:0..n" or attribute["multiplicity"] == "M:1..n":
        return "list"
    if (
        is_a_float_class(class_name)
        or class_name == "String"
        or class_name == "Boolean"
        or class_name == "Integer"
        or is_an_enum_class(class_name)
    ):
        return "primitive"
    else:
        return "class"


# We need to keep track of which class types are secretly float
# primitives. We will use a different template to create the class
# definitions, and we will read them from the file directly into
# an attribute instead of creating a class.
float_classes = {}


def set_float_classes(new_float_classes):
    for new_class in new_float_classes:
        float_classes[new_class] = new_float_classes[new_class]


def is_a_float_class(name):
    if name in float_classes:
        return float_classes[name]


enum_classes = {}


def set_enum_classes(new_enum_classes):
    for new_class in new_enum_classes:
        enum_classes[new_class] = new_enum_classes[new_class]


def is_an_enum_class(name):
    if name in enum_classes:
        return enum_classes[name]


# These insert_ functions are used to generate the entries in the dynamic_switch
# maps, for use in assignments.cpp and Task.cpp
# TODO: implement this as one function, determine in template if it should be called.
# TODO: reorganize json object so we don't have to keep doing the same processing.
def insert_assign_fn(text, render):
    attribute_txt = render(text)
    attribute_json = eval(attribute_txt)
    primitive = attribute_type(attribute_json) == "primitive"
    label = attribute_json["label"]
    class_name = attribute_json["domain"]
    if primitive:
        return "OUTPUT FROM insert_assign_fn" + label + " in " + class_name + "\n"
    else:
        return "primitive OUTPUT FROM insert_assign_fn" + label + " in " + class_name + "\n"


def get_dataType_and_range(attribute):
    _range = _dataType = ""
    if "range" in attribute:
        _range = attribute["range"]
    if "dataType" in attribute:
        _dataType = attribute["dataType"]
    return (_range, _dataType)


# These create_ functions are used to generate the implementations for
# the entries in the dynamic_switch maps referenced in assignments.cpp and Task.cpp
def create_class_assign(text, render):
    # TODO REMOVE:
    return ""
    attribute_txt = render(text)
    attribute_json = eval(attribute_txt)
    assign = ""
    attribute_class = attribute_json["class_name"]
    if attribute_type(attribute_json) == "primitive":
        return ""
    if attribute_json["multiplicity"] == "M:0..n" or attribute_json["multiplicity"] == "M:1..n":
        assign = (
            """
        OUTPUT FROM create_class_assign case 1
            with Label as LABEL
            and Object Class Label as OBJECT_CLASS_LABEL
            and Object Class as OBJECT_CLASS
            and Attribute Class as ATTRIBUTE_CLASS
    """.replace(
                "OBJECT_CLASS", attribute_json["domain"]
            )
            .replace("ATTRIBUTE_CLASS", attribute_class)
            .replace("LABEL", attribute_json["label"])
        )
    elif (
        "inverseRole" in attribute_json
        and "associationUsed" in attribute_json
        and attribute_json["associationUsed"] != "No"
    ):
        inverse = attribute_json["inverseRole"].split(".")
        assign = (
            """
        OUTPUT FROM create_class_assign case 2
            with Object Class Label as OBJECT_CLASS_LABEL
            and Object Class as OBJECT_CLASS
            and Attribute Class as ATTRIBUTE_CLASS
            and Inversec as INVERSEC
            and Inversel as INVERSEL
	""".replace(  # noqa: E101,W191
                "OBJECT_CLASS", attribute_json["domain"]
            )
            .replace("ATTRIBUTE_CLASS", attribute_class)
            .replace("LABEL", attribute_json["label"])
            .replace("INVERSEC", inverse[0])
            .replace("INVERSEL", inverse[1])
        )
    else:
        assign = (
            """
        OUTPUT FROM create_class_assign case 3
            with Label as LABEL
            and Object Class as OBJECT_CLASS
            and Attribute Class as ATTRIBUTE_CLASS
	""".replace(  # noqa: E101,W191
                "OBJECT_CLASS", attribute_json["domain"]
            )
            .replace("ATTRIBUTE_CLASS", attribute_class)
            .replace("LABEL", attribute_json["label"])
        )
    return assign


def create_assign(text, render):
    attribute_txt = render(text)
    attribute_json = eval(attribute_txt)
    assign = ""
    _class = attribute_json["class_name"]
    if not attribute_type(attribute_json) == "primitive":
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


# Some names are encoded as #name or http://some-url#name
# This function returns the name
def _get_rid_of_hash(name):
    tokens = name.split("#")
    if len(tokens) == 1:
        return tokens[0]
    if len(tokens) > 1:
        return tokens[1]
    return name


def attribute_decl(text, render):
    attribute_txt = render(text)
    attribute_json = eval(attribute_txt)
    return _attribute_decl(attribute_json)


def _attribute_decl(attribute):
    _type = attribute_type(attribute)
    _class = attribute["class_name"]
    if _type == "primitive":
        return _class
    if _type == "list":
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
            _type = attribute_type(attribute)
            class_name = attribute["class_name"]
            if class_name != "" and class_name not in unique:
                unique[class_name] = _type
    for clarse in unique:
        if unique[clarse] == "primitive":
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
            _type = attribute_type(attribute)
            class_name = attribute["class_name"]
            if class_name != "" and class_name not in unique:
                unique[class_name] = _type
    for clarse in unique:
        if unique[clarse] == "class" or unique[clarse] == "list":
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
    # the default value is either None or [] depending on the mutliplicity. See also write_python_files
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
    "String",
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

    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        basepath, ext = os.path.splitext(filepath)
        basename = os.path.basename(basepath)
        if ext == ".java" and not _is_enum_class(filepath) and basename not in blacklist:
            lines.append(before + 'Map.entry("' + basename + '", new cim4j.' + basename + after + "),\n")
    lines.sort()
    lines[-1] = lines[-1].replace("),", ")")
    for line in lines:
        header.append(line)
    for line in footer:
        header.append(line)
    header_include_filepath = os.path.join(directory, header_include_filename)
    with open(header_include_filepath, "w", encoding="utf-8") as f:
        f.writelines(header)


def resolve_headers(outputPath):
    class_list_header = [
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
        outputPath,
        "CIMClassMap.java",
        class_list_header,
        class_list_footer,
        "        ",
        "()",
        class_blacklist,
    )
