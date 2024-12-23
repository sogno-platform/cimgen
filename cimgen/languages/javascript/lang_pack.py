import os
import chevron
import sys
from importlib.resources import files


def location(version: str) -> str:  # NOSONAR
    return ""


# Setup called only once: make output directory, create base class, create profile class, etc.
# This function makes sure we have somewhere to write the classes.
# cgmes_profile_details contains index, names and uris for each profile.
# We use that to create the header data for the profiles.
def setup(output_path: str, cgmes_profile_details: list[dict], cim_namespace: str) -> None:
    if not os.path.exists(output_path):
        os.makedirs(output_path)
    else:
        for filename in os.listdir(output_path):
            os.remove(os.path.join(output_path, filename))
    _create_base(output_path)
    _create_cgmes_profile(output_path, cgmes_profile_details, cim_namespace)


base = {"base_class": "BaseClass", "class_location": location}

# These are the files that are used to generate the javascript files.
template_files = [{"filename": "handlebars_template.mustache", "ext": ".js"}]
base_template_files = [{"filename": "handlebars_baseclass_template.mustache", "ext": ".js"}]
profile_template_files = [{"filename": "handlebars_cgmesProfile_template.mustache", "ext": ".js"}]

partials = {}


def get_class_location(class_name: str, class_map: dict, version: str) -> str:  # NOSONAR
    return ""


aggregateRenderer: dict[str, str] = {
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


def select_primitive_render_function(class_details: dict) -> str:
    class_name = class_details["class_name"]
    render = ""
    if class_details["is_a_datatype_class"]:
        render = aggregateRenderer["renderFloat"]
    elif class_name in ("Float", "Decimal"):
        render = aggregateRenderer["renderFloat"]
    elif class_name == "String":
        render = aggregateRenderer["renderString"]
    elif class_name == "Boolean":
        render = aggregateRenderer["renderBoolean"]
    elif class_name == "Date":
        # TODO: Implementation Required!
        render = aggregateRenderer["renderString"]
    elif class_name == "DateTime":
        # TODO: Implementation Required!
        render = aggregateRenderer["renderString"]
    elif class_name == "Integer":
        # TODO: Implementation Required!
        render = aggregateRenderer["renderString"]
    elif class_name == "MonthDay":
        # TODO: Implementation Required!
        render = aggregateRenderer["renderString"]
    return render


# This is the function that runs the template.
def run_template(output_path: str, class_details: dict) -> None:
    if class_details["class_name"] == "String":
        return

    for index, attribute in enumerate(class_details["attributes"]):
        if not attribute["is_used"]:
            del class_details["attributes"][index]

    renderAttribute = ""
    class_type = _get_class_type(class_details)
    if class_type == "enum":
        renderAttribute = aggregateRenderer["renderInstance"]
    elif class_type == "primitive":
        renderAttribute = select_primitive_render_function(class_details)
    else:
        renderAttribute = aggregateRenderer["renderClass"]
    if renderAttribute == "":
        print("Could not work out render function for: ", class_details["class_name"])
        sys.exit(1)
    class_details["renderAttribute"] = renderAttribute

    for template_info in template_files:
        class_file = os.path.join(output_path, class_details["class_name"] + template_info["ext"])
        _write_templated_file(class_file, class_details, template_info["filename"])


def _write_templated_file(class_file: str, class_details: dict, template_filename: str) -> None:
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
def _create_base(output_path: str) -> None:
    for template_info in base_template_files:
        class_file = os.path.join(output_path, "BaseClass" + template_info["ext"])
        _write_templated_file(class_file, {}, template_info["filename"])


def _create_cgmes_profile(output_path: str, profile_details: list[dict], cim_namespace: str) -> None:
    for template_info in profile_template_files:
        class_file = os.path.join(output_path, "CGMESProfile" + template_info["ext"])
        class_details = {
            "profiles": profile_details,
            "cim_namespace": cim_namespace,
        }
        _write_templated_file(class_file, class_details, template_info["filename"])


def _get_class_type(class_details: dict) -> str:
    if class_details["is_a_primitive_class"] or class_details["is_a_datatype_class"]:
        return "primitive"
    if class_details["is_an_enum_class"]:
        return "enum"
    return "class"


def resolve_headers(path: str, version: str) -> None:  # NOSONAR
    pass
