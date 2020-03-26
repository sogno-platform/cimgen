import os
import chevron
import json

def location(version):
    return "BaseClass.h";

# This just makes sure we have somewhere to write the classes.
def setup(version_path):
    if not os.path.exists(version_path):
        os.makedirs(version_path)

base = {
    "base_class": "BaseClass",
    "class_location": location
}

# These are the files that are used to generate the header and object files.
# There is a template set for the large number of classes that are floats. They
# have unit, multiplier and value attributes in the schema, but only appear in
# the file as a float string.
template_files = [ { "filename": "cpp_header_template.mustache", "ext": ".hpp" },
                   { "filename": "cpp_object_template.mustache", "ext": ".cpp" } ]
float_template_files = [ { "filename": "cpp_float_header_template.mustache", "ext": ".hpp" },
                         { "filename": "cpp_float_object_template.mustache", "ext": ".cpp" } ]

partials = { 'class':                   '{{#langPack.format_class}}{{range}} {{dataType}}{{/langPack.format_class}}',
             'attribute':               '{{#langPack.attribute_decl}}{{.}}{{/langPack.attribute_decl}}',
             'create_init_list':        '{{#langPack.null_init_list}}{{attributes}}{{/langPack.null_init_list}}',
             'create_construct_list':   '{{#langPack.create_construct_list}}{{attributes}}{{/langPack.create_construct_list}}',
	     'insert_assign':           '{{#langPack.insert_assign_fn}}{{.}}{{/langPack.insert_assign_fn}}',
	     'insert_class_assign':     '{{#langPack.insert_class_assign_fn}}{{.}}{{/langPack.insert_class_assign_fn}}',
             'read_istream':            '{{#langPack.create_istream_op}}{{class_name}} {{label}}{{/langPack.create_istream_op}}',
           }

# This is the function that runs the template.
def run_template(version_path, class_details):
    if class_details['is_a_float'] == True:
        templates = float_template_files
    else:
        templates = template_files

    for template_info in templates:
        class_file = os.path.join(version_path, class_details['class_name'] + template_info["ext"])
        if not os.path.exists(class_file):
            with open(class_file, 'w') as file:
                with open(template_info["filename"]) as f:
                    args = {
                        'data': class_details,
                        'template': f,
                        'partials_dict': partials
                    }
                    output = chevron.render(**args)
                file.write(output)

# This function determines how the attribute code will be implemented.
#  - attributes which are primitives will be read from the file and
#    stored in the class object we are reading at the time
#  - attributes which are classes will be stored as pointers to the
#    actual class, which will be read from another part of the file.
#  - attributes with multiplicity of 1..n or 0..n will be std::lists
#    of pointers to classes read from a different part of the file
def attribute_type(attribute):
    (_range, _dataType) =  get_dataType_and_range(attribute)
    class_name = _format_class([_range, _dataType])
    if attribute["multiplicity"] == 'M:0..n' or attribute["multiplicity"] == 'M:1..n':
        return "list"
    if is_a_float_class(class_name) or class_name == "String" or class_name == "Boolean" or class_name == "Integer":
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

# These insert_ functions are used to generate the entries in the dynamic_switch
# maps, for use in assignments.cpp and Task.cpp
# TODO: implement this as one function, determine in template if it should be called.
# TODO: reorganize json object so we don't have to keep doing the same processing.
def insert_assign_fn(text, render):
    attribute_txt = render(text)
    attribute_json = eval(attribute_txt)
    if not attribute_type(attribute_json) == "primitive":
        return ''
    assign = ""
    label = attribute_json['label']
    (_range, _dataType) =  get_dataType_and_range(attribute_json)
    attr_class = _format_class([_range, _dataType])
    class_name = attribute_json['domain']
    return 'assign_map.insert(std::make_pair(std::string("cim:' + class_name + '.' + label + '"), &assign_' + class_name + '_' + label + '));\n'

def insert_class_assign_fn(text, render):
    attribute_txt = render(text)
    attribute_json = eval(attribute_txt)
    if attribute_type(attribute_json) == "primitive":
        return ''
    assign = ""
    (_range, _dataType) =  get_dataType_and_range(attribute_json)
    label = attribute_json['label']
    attr_class = _format_class([_range, _dataType])
    class_name = attribute_json['domain']
    return 'assign_map.insert(std::make_pair(std::string("cim:' + class_name + '.' + label + '"), &assign_' + class_name + '_' + label + '));\n'

def get_dataType_and_range(attribute):
    _range = _dataType = ""
    if "range" in attribute:
        _range = attribute["range"]
    if "dataType" in attribute:
        _dataType = attribute["dataType"]
    return (_range, _dataType)

# These create_ functions are used to generate the implementations for
# the entries in the dynamic_switch maps in assignments.cpp and Task.cpp
def create_class_assign(text, render):
    attribute_txt = render(text)
    attribute_json = eval(attribute_txt)
    assign = ""
    (_range, _dataType) =  get_dataType_and_range(attribute_json)
    attribute_class = _format_class([_range, _dataType])
    if attribute_type(attribute_json) == "primitive":
        return ''
    if attribute_json["multiplicity"] == "M:0..n" or attribute_json["multiplicity"] == "M:1..n":
        assign = """
bool assign_OBJECT_CLASS_LABEL(BaseClass* BaseClass_ptr1, BaseClass* BaseClass_ptr2) {
	if(OBJECT_CLASS* element = dynamic_cast<OBJECT_CLASS*>(BaseClass_ptr1)) {
		if(dynamic_cast<ATTRIBUTE_CLASS*>(BaseClass_ptr2) != nullptr) {
                        element->_LABEL.push_back(dynamic_cast<ATTRIBUTE_CLASS*>(BaseClass_ptr2));
			return true;
		}
	}
	return false;
}""".replace("OBJECT_CLASS", attribute_json["domain"]).replace("ATTRIBUTE_CLASS", _get_rid_of_hash(attribute_json["range"])).replace("LABEL", attribute_json["label"])
    else:
        assign = """
bool assign_OBJECT_CLASS_LABEL(BaseClass* BaseClass_ptr1, BaseClass* BaseClass_ptr2) {
	if(OBJECT_CLASS* element = dynamic_cast<OBJECT_CLASS*>(BaseClass_ptr1)) {
                element->_LABEL = dynamic_cast<ATTRIBUTE_CLASS*>(BaseClass_ptr2);
                if(element->_LABEL != nullptr)
                        return true;
        }
        return false;
}""".replace("OBJECT_CLASS", attribute_json["domain"]).replace("ATTRIBUTE_CLASS", attribute_class).replace("LABEL", attribute_json["label"])

    return assign

def create_assign(text, render):
    attribute_txt = render(text)
    attribute_json = eval(attribute_txt)
    assign = ""
    (_range, _dataType) =  get_dataType_and_range(attribute_json)
    _class = _format_class([_range, _dataType])
    if not attribute_type(attribute_json) == "primitive":
        return ''
    if _class == "Boolean" or _class == "Integer" or _class == "Float" or is_a_float_class(_class):
        assign = """
bool assign_CLASS_LABEL(std::stringstream &buffer, BaseClass* BaseClass_ptr1) {
	if(CLASS* element = dynamic_cast<CLASS*>(BaseClass_ptr1)) {
                buffer >> element->_LABEL;
                if(buffer.fail())
                        return false;
                else
                        return true;
        }
        else
                return false;
}""".replace("CLASS", attribute_json["domain"]).replace("LABEL", attribute_json["label"])
    elif _class == "String":
        assign = """
bool assign_CLASS_LABEL(std::stringstream &buffer, BaseClass* BaseClass_ptr1) {
	if(CLASS* element = dynamic_cast<CLASS*>(BaseClass_ptr1)) {
		element->_LABEL = buffer.str();
		if(buffer.fail())
			return false;
		else
			return true;
	}
	return false;
}""".replace("CLASS", attribute_json["domain"]).replace("LABEL", attribute_json["label"])

    return assign

# What class is this attribute?
def format_class(text, render):
    result = render(text)
    tokens = result.split(' ')
    if len(tokens) < 2:
        return None;
    else:
        return _format_class(tokens)

def _format_class(tokens):
    if (tokens[0]) == '':
        val = _get_rid_of_hash(tokens[1])
        return val
    else:
        val = _get_rid_of_hash(tokens[0])
        return val

# Some names are encoded as #name or http://some-url#name
# This function returns the name
def _get_rid_of_hash(name):
    tokens = name.split('#')
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
    (_range, _dataType) =  get_dataType_and_range(attribute)
    _class = _format_class([_range, _dataType])
    if _type == "primitive":
        return _class
    if _type == "list":
        return "std::list<" + _class + "*>"
    else:
        return _class + '*'

def _create_attribute_includes(text, render):
    unique = []
    include_string = ""
    inputText = render(text)
    jsonString = inputText.replace("'", "\"")
    jsonStringNoHtmlEsc = jsonString.replace("&quot;", "\"")
    if jsonStringNoHtmlEsc != None and jsonStringNoHtmlEsc != "":
        attributes = json.loads(jsonStringNoHtmlEsc)
        for attribute in attributes:
            _type = attribute_type(attribute)
            (_range, _dataType) =  get_dataType_and_range(attribute)
            class_name = _format_class([_range, _dataType])
            if class_name not in unique:
                unique.append({'name': class_name, 'type': _type})
    for clarse in unique:
        if clarse['name'] != "":
            if clarse['type'] == "class" or clarse['type'] == "list":
                include_string += '\nclass ' + clarse['name'] + ';'
            else:
                include_string += '\n#include "' + clarse['name'] + '.hpp"'

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
    if dataType in ['M:1', 'M:0..1', 'M:1..1', 'M:0..n', 'M:1..n', ''] or 'M:' in dataType:
        return '0'
    dataType = dataType.split('#')[1]
    if dataType in ['integer', 'Integer']:
        return '0'
    elif dataType in ['String', 'DateTime', 'Date']:
        return "''"
    elif dataType == 'Boolean':
        return 'false'
    else:
        return 'nullptr'


