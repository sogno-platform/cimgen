import os
import chevron
import sys
from importlib.resources import files


def location(version):
    return "BaseClass.hpp"


# Setup called only once: make output directory, create base class, create profile class, etc.
# This function makes sure we have somewhere to write the classes.
# cgmes_profile_details contains index, names und uris for each profile.
# We use that to create the header data for the profiles.
def setup(output_path, cgmes_profile_details):
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    else:
        for filename in os.listdir(output_path):
            os.remove(os.path.join(output_path, filename))
    _create_base(output_path)
    _create_cgmes_profile(output_path, cgmes_profile_details)


base = {"base_class": "BaseClass", "class_location": location}

# These are the files that are used to generate the javascript files.
template_files = [{"filename": "handlebars_template.mustache", "ext": ".js"}]
base_template_files = [{"filename": "handlebars_baseclass_template.mustache", "ext": ".js"}]
profile_template_files = [{"filename": "handlebars_cgmesProfile_template.mustache", "ext": ".js"}]

partials = {}


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


def get_class_location(class_name, class_map, version):
    pass


aggregateRenderer = {
    "renderFloat": "static renderAsAttribute(data) {\n\
        return templates.handlebars_cim_render_float(data)\n\
    }",
    "renderString": "static renderAsAttribute(data) {\n\
        return templates.handlebars_cim_render_string(data)\n\
    }",
    "renderBoolean": "static renderAsAttribute(data) {\n\
        return templates.handlebars_cim_render_boolean(data)\n\
    }",
    "renderInteger": "static renderAsAttribute(data) {\n\
        return templates.handlebars_cim_render_string(data)\n\
    }",
    "renderInstance": "static renderAsAttribute(matchingComponents) {\n\
        let template = templates.handlebars_cim_instance_type;\n\
        matchingComponents.aggregates = possibleValues;\n\
        for (let index in matchingComponents.aggregates) {\n\
            if (matchingComponents.value) {\n\
                let value = matchingComponents.value['rdf:resource']\n\
                let candidate = matchingComponents.aggregates[index].value;\n\
                if(candidate !== undefined && common.getRidOfHash(value) == candidate) {\n\
                    matchingComponents.aggregates[index].selected = 'selected';\n\
                }\n\
                else {\n\
                    delete matchingComponents.aggregates[index].selected;\n\
                }\n\
            }\n\
        }\n\
        return template(matchingComponents);\n\
    }",
    "renderClass": "static renderAsAttribute(matchingComponents) {\n\
        let template = templates.handlebars_cim_update_complex_type;\n\
        return template(matchingComponents);\n\
    }",
}


def selectPrimitiveRenderFunction(primitive):
    render = ""
    if is_a_float_class(primitive):
        render = aggregateRenderer["renderFloat"]
    elif primitive == "String":
        render = aggregateRenderer["renderString"]
    elif primitive == "Boolean":
        render = aggregateRenderer["renderBoolean"]
    elif primitive == "Date":
        # TODO: Implementation Required!
        render = aggregateRenderer["renderString"]
    elif primitive == "DateTime":
        # TODO: Implementation Required!
        render = aggregateRenderer["renderString"]
    elif primitive == "Decimal":
        # TODO: Implementation Required!
        render = aggregateRenderer["renderString"]
    elif primitive == "Integer":
        # TODO: Implementation Required!
        render = aggregateRenderer["renderString"]
    elif primitive == "MonthDay":
        # TODO: Implementation Required!
        render = aggregateRenderer["renderString"]
    return render


# This is the function that runs the template.
def run_template(output_path, class_details):

    class_details["is_not_terminal"] = class_details["class_name"] != "Terminal"
    for attr in class_details["attributes"]:
        if "range" in attr:
            attr["attributeClass"] = _get_rid_of_hash(attr["range"])
        elif "dataType" in attr:
            attr["attributeClass"] = _get_rid_of_hash(attr["dataType"])

    for index, attribute in enumerate(class_details["attributes"]):
        if is_an_unused_attribute(attribute):
            del class_details["attributes"][index]

    renderAttribute = ""
    attrType = attribute_type(class_details)
    if attrType == "enum":
        renderAttribute = aggregateRenderer["renderInstance"]
    elif attrType == "primitive":
        renderAttribute = selectPrimitiveRenderFunction(class_details["class_name"])
    else:
        renderAttribute = aggregateRenderer["renderClass"]
    if renderAttribute == "":
        print("Could not work out render function for: ", class_details["class_name"])
        sys.exit(1)
    class_details["renderAttribute"] = renderAttribute

    for template_info in template_files:
        class_file = os.path.join(output_path, class_details["class_name"] + template_info["ext"])
        _write_templated_file(class_file, class_details, template_info["filename"])


def _write_templated_file(class_file, class_details, template_filename):
    with open(class_file, "w", encoding="utf-8") as file:
        templates = files("cimgen.languages.javascript.templates")
        with templates.joinpath(template_filename).open(encoding="utf-8") as f:
            args = {
                "data": class_details,
                "template": f,
                "partials_dict": partials,
            }
            output = chevron.render(**args)
        file.write(output)


# creates the Base class file, all classes inherit from this class
def _create_base(output_path):
    for template_info in base_template_files:
        class_file = os.path.join(output_path, "BaseClass" + template_info["ext"])
        _write_templated_file(class_file, {}, template_info["filename"])


def _create_cgmes_profile(output_path, profile_details):
    for template_info in profile_template_files:
        class_file = os.path.join(output_path, "CGMESProfile" + template_info["ext"])
        _write_templated_file(class_file, {"profiles": profile_details}, template_info["filename"])


def is_an_unused_attribute(attr_details, debug=False):
    is_unused = (
        "inverseRole" in attr_details and "associationUsed" in attr_details and attr_details["associationUsed"] == "No"
    )
    if debug and is_unused:
        print(attr_details["about"], " is_unused: ", is_unused)
    return is_unused


def attribute_type(class_details):
    class_name = class_details["class_name"]
    if is_a_float_class(class_name) or class_name == "String" or class_name == "Boolean" or class_name == "Integer":
        return "primitive"
    if is_an_enum_class(class_name):
        return "enum"
    return "class"


# This function returns the name
def _get_rid_of_hash(name):
    tokens = name.split("#")
    if len(tokens) == 1:
        return tokens[0]
    if len(tokens) > 1:
        return tokens[1]
    return name


def resolve_headers(output_path):
    pass
