import os
import chevron
import json
from importlib.resources import files


def location(version):
    return "BaseClass.hpp"


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


def get_class_location(class_name, class_map, version):
    pass


partials = {
    "attribute": "{{#langPack.attribute_decl}}{{.}}{{/langPack.attribute_decl}}",
    "label": "{{#langPack.label}}{{label}}{{/langPack.label}}",
    "create_init_list": "{{#langPack.null_init_list}}{{attributes}}{{/langPack.null_init_list}}",
    "create_construct_list": "{{#langPack.create_construct_list}}{{attributes}}{{/langPack.create_construct_list}}",
    "insert_assign": "{{#langPack.insert_assign_fn}}{{.}}{{/langPack.insert_assign_fn}}",
    "insert_class_assign": "{{#langPack.insert_class_assign_fn}}{{.}}{{/langPack.insert_class_assign_fn}}",
    "read_istream": "{{#langPack.create_istream_op}}{{class_name}} {{label}}{{/langPack.create_istream_op}}",
}


# This is the function that runs the template.
def run_template(outputPath, class_details):

    if class_details["is_a_float"] == True:
        templates = float_template_files
    elif class_details["has_instances"] == True:
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
                templates = files("cimgen.languages.cpp.templates")
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
    if not attribute_type(attribute_json) == "primitive":
        return ""
    label = attribute_json["label"]
    class_name = attribute_json["domain"]
    return (
        'assign_map.insert(std::make_pair(std::string("cim:'
        + class_name
        + "."
        + label
        + '"), &assign_'
        + class_name
        + "_"
        + label
        + "));\n"
    )


def insert_class_assign_fn(text, render):
    attribute_txt = render(text)
    attribute_json = eval(attribute_txt)
    if attribute_type(attribute_json) == "primitive":
        return ""
    label = attribute_json["label"]
    class_name = attribute_json["domain"]
    return (
        'assign_map.insert(std::make_pair(std::string("cim:'
        + class_name
        + "."
        + label
        + '"), &assign_'
        + class_name
        + "_"
        + label
        + "));\n"
    )


def get_dataType_and_range(attribute):
    _range = _dataType = ""
    if "range" in attribute:
        _range = attribute["range"]
    if "dataType" in attribute:
        _dataType = attribute["dataType"]
    return (_range, _dataType)


def create_nullptr_assigns(text, render):
    attributes_txt = render(text)
    if attributes_txt.strip() == "":
        return ""
    else:
        attributes_json = eval(attributes_txt)
        nullptr_init_string = ": "
        for attribute in attributes_json:
            name = attribute["label"]
            if attribute_type(attribute) == "primitive":
                continue
            if attribute["multiplicity"] == "M:0..n" or attribute["multiplicity"] == "M:1..n":
                continue
            else:
                nullptr_init_string += "LABEL(nullptr), ".replace("LABEL", attribute["label"])

    if len(nullptr_init_string) > 2:
        return nullptr_init_string[:-2]
    else:
        return ""


# These create_ functions are used to generate the implementations for
# the entries in the dynamic_switch maps referenced in assignments.cpp and Task.cpp
def create_class_assign(text, render):
    attribute_txt = render(text)
    attribute_json = eval(attribute_txt)
    assign = ""
    attribute_class = attribute_json["class_name"]
    if attribute_type(attribute_json) == "primitive":
        return ""
    if attribute_json["multiplicity"] == "M:0..n" or attribute_json["multiplicity"] == "M:1..n":
        assign = (
            """
bool assign_OBJECT_CLASS_LABEL(BaseClass* BaseClass_ptr1, BaseClass* BaseClass_ptr2) {
	if(OBJECT_CLASS* element = dynamic_cast<OBJECT_CLASS*>(BaseClass_ptr1)) {
		if(dynamic_cast<ATTRIBUTE_CLASS*>(BaseClass_ptr2) != nullptr) {
                        element->LABEL.push_back(dynamic_cast<ATTRIBUTE_CLASS*>(BaseClass_ptr2));
			return true;
		}
	}
	return false;
}""".replace(
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
bool assign_INVERSEC_INVERSEL(BaseClass*, BaseClass*);
bool assign_OBJECT_CLASS_LABEL(BaseClass* BaseClass_ptr1, BaseClass* BaseClass_ptr2) {
	if(OBJECT_CLASS* element = dynamic_cast<OBJECT_CLASS*>(BaseClass_ptr1)) {
                element->LABEL = dynamic_cast<ATTRIBUTE_CLASS*>(BaseClass_ptr2);
                if(element->LABEL != nullptr)
                        return assign_INVERSEC_INVERSEL(BaseClass_ptr2, BaseClass_ptr1);
        }
        return false;
}""".replace(
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
bool assign_OBJECT_CLASS_LABEL(BaseClass* BaseClass_ptr1, BaseClass* BaseClass_ptr2) {
	if(OBJECT_CLASS* element = dynamic_cast<OBJECT_CLASS*>(BaseClass_ptr1)) {
                element->LABEL = dynamic_cast<ATTRIBUTE_CLASS*>(BaseClass_ptr2);
                if(element->LABEL != nullptr)
                        return true;
        }
        return false;
}""".replace(
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
        assign = (
            """
bool assign_CLASS_LABEL(std::stringstream &buffer, BaseClass* BaseClass_ptr1) {
	if(CLASS* element = dynamic_cast<CLASS*>(BaseClass_ptr1)) {
                buffer >> element->LBL_WO_KEYWORD;
                if(buffer.fail())
                        return false;
                else
                        return true;
        }
        else
                return false;
}""".replace(
                "CLASS", attribute_json["domain"]
            )
            .replace("LABEL", attribute_json["label"])
            .replace("LBL_WO_KEYWORD", label_without_keyword)
        )
    else:
        assign = """
bool assign_CLASS_LABEL(std::stringstream &buffer, BaseClass* BaseClass_ptr1) {
	if(CLASS* element = dynamic_cast<CLASS*>(BaseClass_ptr1)) {
		element->LABEL = buffer.str();
		if(buffer.fail())
			return false;
		else
			return true;
	}
	return false;
}""".replace(
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
        return "CIMPP::" + _class
    if _type == "list":
        return "std::list<CIMPP::" + _class + "*>"
    else:
        return "CIMPP::" + _class + "*"


def _create_attribute_includes(text, render):
    unique = {}
    include_string = ""
    inputText = render(text)
    jsonString = inputText.replace("'", '"')
    jsonStringNoHtmlEsc = jsonString.replace("&quot;", '"')
    if jsonStringNoHtmlEsc != None and jsonStringNoHtmlEsc != "":
        attributes = json.loads(jsonStringNoHtmlEsc)
        for attribute in attributes:
            _type = attribute_type(attribute)
            class_name = attribute["class_name"]
            if class_name != "" and class_name not in unique:
                unique[class_name] = _type
    for clarse in unique:
        if unique[clarse] == "primitive":
            include_string += '\n#include "' + clarse + '.hpp"'

    return include_string


def _create_attribute_class_declarations(text, render):
    unique = {}
    include_string = ""
    inputText = render(text)
    jsonString = inputText.replace("'", '"')
    jsonStringNoHtmlEsc = jsonString.replace("&quot;", '"')
    if jsonStringNoHtmlEsc != None and jsonStringNoHtmlEsc != "":
        attributes = json.loads(jsonStringNoHtmlEsc)
        for attribute in attributes:
            _type = attribute_type(attribute)
            class_name = attribute["class_name"]
            if class_name != "" and class_name not in unique:
                unique[class_name] = _type
    for clarse in unique:
        if unique[clarse] == "class" or unique[clarse] == "list":
            include_string += "\nclass " + clarse + ";"

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
        if ext == ".hpp" and not _is_enum_class(filepath) and not basename in blacklist:
            lines.append(before + basename + after)
    lines.sort()
    for line in lines:
        header.append(line)
    for line in footer:
        header.append(line)
    header_include_filepath = os.path.join(directory, header_include_filename)
    with open(header_include_filepath, "w", encoding="utf-8") as f:
        f.writelines(header)


def resolve_headers(outputPath):
    class_list_header = [
        "#ifndef CIMCLASSLIST_H\n",
        "#define CIMCLASSLIST_H\n",
        "using namespace CIMPP;\n",
        "#include <list>\n",
        "static std::list<BaseClassDefiner> CIMClassList = {\n",
    ]
    class_list_footer = [
        "    UnknownType::declare() };\n",
        "#endif // CIMCLASSLIST_H\n",
    ]

    _create_header_include_file(
        outputPath,
        "CIMClassList.hpp",
        class_list_header,
        class_list_footer,
        "    ",
        "::declare(),\n",
        class_blacklist,
    )

    iec61970_header = ["#ifndef IEC61970_H\n", "#define IEC61970_H\n"]
    iec61970_footer = ['#include "UnknownType.hpp"\n', "#endif"]

    _create_header_include_file(
        outputPath,
        "IEC61970.hpp",
        iec61970_header,
        iec61970_footer,
        '#include "',
        '.hpp"\n',
        iec61970_blacklist,
    )
