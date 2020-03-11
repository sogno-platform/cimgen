import os
import json

def location(version):
     return "BaseClass.h";

base = {
    "base_class": "BaseClass",
    "class_location": location
}

template_files = [ { "filename": "cpp_header_template.mustache", "ext": ".hpp" },
                   { "filename": "cpp_object_template.mustache", "ext": ".cpp" } ]

partials = { 'class':          '{{#langPack.format_class}}{{range}} {{dataType}}{{/langPack.format_class}}',
             'create_init_list': '{{#langPack.null_init_list}}{{attributes}}{{/langPack.null_init_list}}',
             'create_construct_list': '{{#langPack.create_construct_list}}{{attributes}}{{/langPack.create_construct_list}}',
           }

def get_dataType_and_range(attribute):
    _range = _datatype = ""
    if "range" in attribute:
        _range = attribute["range"]
    if "dataType" in attribute:
        _dataType = attribute["dataType"]
    return (_range, _dataType)

def create_construct_list(text, render):
    attributes_txt = render(text)
    result = ""
    if (attributes_txt != ""):
        attributes_json = eval(attributes_txt)
        for a in attributes_json[:-1]:
            (_range, _dataType) =  get_dataType_and_range(a)
            result += _format_class([_range, _dataType]) + ' *_' + a["label"]  + '_, '
        (_range, _dataType) =  get_dataType_and_range(attributes_json[-1])
        result += _format_class([_range, _dataType]) + ' *_' + attributes_json[-1]["label"] + '_'

    return result

def null_init_list(text, render):
    attributes_txt = render(text)
    result = ""
    if (attributes_txt != ""):
        attributes_json = eval(attributes_txt)
        for a in attributes_json[:-1]:
            result += "_" + a["label"] + "(" + set_default(a["dataType"]) + "), "
        result += "_" + attributes_json[-1]["label"] + "(" + set_default(attributes_json[-1]["dataType"]) + ")"

    return result

def format_class(text, render):
    result = render(text)
    tokens = result.split(' ')
    if len(tokens) < 2:
        return None;
    else:
        return _format_class(tokens)

def _format_class(tokens):
    if (tokens[0]) == '':
        val = _get_rid_of_hash(tokens[1]);
        return val
    else:
        val = _get_rid_of_hash(tokens[0]);
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

def _create_attribute_includes(text, render):
    unique = []
    include_string = ""
    inputText = render(text)
    jsonString = inputText.replace("'", "\"")
    jsonStringNoHtmlEsc = jsonString.replace("&quot;", "\"")
    if jsonStringNoHtmlEsc != None and jsonStringNoHtmlEsc != "":
        attributes = json.loads(jsonStringNoHtmlEsc)
        for attribute in attributes:
            clarse = ''
            if "range" in attribute:
                clarse = _get_rid_of_hash(attribute["range"])
            elif "dataType" in attribute:
                clarse = _get_rid_of_hash(attribute["dataType"])
            if clarse not in unique:
                unique.append(clarse)
    for clarse in unique:
        if clarse != "":
            if clarse == "String":
                include_string += '\n#include "String.hpp"'
            else:
                include_string += '\nclass ' + clarse + ';'

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
        # everything else should be a float
        return '0'

def setup(version_path):
    if not os.path.exists(version_path):
        os.makedirs(version_path)

