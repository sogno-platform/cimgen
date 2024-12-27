import chevron
import json
import shutil
from pathlib import Path
from importlib.resources import files
from typing import Callable


# Setup called only once: make output directory, create base class, create profile class, etc.
# This just makes sure we have somewhere to write the classes.
# cgmes_profile_details contains index, names and uris for each profile.
# We use that to create the header data for the profiles.
def setup(output_path: str, cgmes_profile_details: list[dict], cim_namespace: str) -> None:
    source_dir = Path(__file__).parent
    dest_dir = Path(output_path)
    for file in dest_dir.glob("**/*.[ch]*"):
        file.unlink()
    # Add all hardcoded utils and create parent dir
    for file in source_dir.glob("static/*.[ch]*"):
        dest_file = dest_dir / file.relative_to(source_dir)
        dest_file.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(file, dest_file)
    _create_cgmes_profile(dest_dir, cgmes_profile_details, cim_namespace)


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
string_template_files = [
    {"filename": "cpp_string_header_template.mustache", "ext": ".hpp"},
    {"filename": "cpp_string_object_template.mustache", "ext": ".cpp"},
]
profile_template_files = [
    {"filename": "cpp_cgmesProfile_header_template.mustache", "ext": ".hpp"},
    {"filename": "cpp_cgmesProfile_object_template.mustache", "ext": ".cpp"},
]

partials = {
    "attribute_decl": "{{#lang_pack.attribute_decl}}{{.}}{{/lang_pack.attribute_decl}}",
    "label_without_keyword": "{{#lang_pack.label_without_keyword}}{{label}}{{/lang_pack.label_without_keyword}}",
    "insert_assign": "{{#lang_pack.insert_assign_fn}}{{.}}{{/lang_pack.insert_assign_fn}}",
    "insert_class_assign": "{{#lang_pack.insert_class_assign_fn}}{{.}}{{/lang_pack.insert_class_assign_fn}}",
    "insert_get": "{{#lang_pack.insert_get_fn}}{{.}}{{/lang_pack.insert_get_fn}}",
    "insert_class_get": "{{#lang_pack.insert_class_get_fn}}{{.}}{{/lang_pack.insert_class_get_fn}}",
    "insert_enum_get": "{{#lang_pack.insert_enum_get_fn}}{{.}}{{/lang_pack.insert_enum_get_fn}}",
    "create_nullptr_assigns": "{{#lang_pack.create_nullptr_assigns}}"
    " {{attributes}} {{/lang_pack.create_nullptr_assigns}} {};",
    "create_assign": "{{#lang_pack.create_assign}}{{.}}{{/lang_pack.create_assign}}",
    "create_class_assign": "{{#lang_pack.create_class_assign}}{{.}}{{/lang_pack.create_class_assign}}",
    "create_get": "{{#lang_pack.create_get}}{{.}}{{/lang_pack.create_get}}",
    "create_class_get": "{{#lang_pack.create_class_get}}{{.}}{{/lang_pack.create_class_get}}",
    "create_enum_get": "{{#lang_pack.create_enum_get}}{{.}}{{/lang_pack.create_enum_get}}",
    "create_attribute_includes": "{{#lang_pack.create_attribute_includes}}"
    "{{attributes}}{{/lang_pack.create_attribute_includes}}",
    "create_attribute_class_declarations": "{{#lang_pack.create_attribute_class_declarations}}"
    "{{attributes}}{{/lang_pack.create_attribute_class_declarations}}",
    "set_default": "{{#lang_pack.set_default}}{{datatype}}{{/lang_pack.set_default}}",
}


def get_base_class() -> str:
    return "BaseClass"


def get_class_location(class_name: str, class_map: dict, version: str) -> str:  # NOSONAR
    return ""


# This is the function that runs the template.
def run_template(output_path: str, class_details: dict) -> None:

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
        class_file = Path(output_path) / (class_details["class_name"] + template_info["ext"])
        _write_templated_file(class_file, class_details, template_info["filename"])


def _write_templated_file(class_file: Path, class_details: dict, template_filename: str) -> None:
    with class_file.open("w", encoding="utf-8") as file:
        templates = files("cimgen.languages.cpp.templates")
        with templates.joinpath(template_filename).open(encoding="utf-8") as f:
            args = {
                "data": class_details,
                "template": f,
                "partials_dict": partials,
            }
            output = chevron.render(**args)
        file.write(output)


def _create_cgmes_profile(output_path: Path, profile_details: list[dict], cim_namespace: str) -> None:
    for template_info in profile_template_files:
        class_file = output_path / ("CGMESProfile" + template_info["ext"])
        class_details = {
            "profiles": profile_details,
            "cim_namespace": cim_namespace,
        }
        _write_templated_file(class_file, class_details, template_info["filename"])


# This function just allows us to avoid declaring a variable called 'switch',
# which is in the definition of the ExcBBC class.
def label_without_keyword(text: str, render: Callable[[str], str]) -> str:
    label = render(text)
    return _get_label_without_keyword(label)


def _get_label_without_keyword(label: str) -> str:
    if label == "switch":
        return "_switch"
    return label


# These insert_ functions are used to generate the entries in the dynamic_switch
# maps, for use in assignments.cpp and Task.cpp
# TODO: implement this as one function, determine in template if it should be called.
# TODO: reorganize json object so we don't have to keep doing the same processing.
def insert_assign_fn(text: str, render: Callable[[str], str]) -> str:
    attribute_txt = render(text)
    attribute_json = eval(attribute_txt)
    if not _attribute_is_primitive_or_datatype_or_enum(attribute_json):
        return ""
    label = attribute_json["label"]
    class_name = attribute_json["domain"]
    return (
        '	assign_map.insert(std::make_pair(std::string("cim:'
        + class_name
        + "."
        + label
        + '"), &assign_'
        + class_name
        + "_"
        + label
        + "));\n"
    )


def insert_class_assign_fn(text: str, render: Callable[[str], str]) -> str:
    attribute_txt = render(text)
    attribute_json = eval(attribute_txt)
    if _attribute_is_primitive_or_datatype_or_enum(attribute_json):
        return ""
    label = attribute_json["label"]
    class_name = attribute_json["domain"]
    return (
        '	assign_map.insert(std::make_pair(std::string("cim:'
        + class_name
        + "."
        + label
        + '"), &assign_'
        + class_name
        + "_"
        + label
        + "));\n"
    )


def insert_get_fn(text: str, render: Callable[[str], str]) -> str:
    attribute_txt = render(text)
    attribute_json = eval(attribute_txt)
    if not _attribute_is_primitive_or_datatype(attribute_json):
        return ""
    label = attribute_json["label"]
    class_name = attribute_json["domain"]
    return '	get_map.emplace("cim:' + class_name + "." + label + '", &get_' + class_name + "_" + label + ");\n"


def insert_class_get_fn(text: str, render: Callable[[str], str]) -> str:
    attribute_txt = render(text)
    attribute_json = eval(attribute_txt)
    if _attribute_is_primitive_or_datatype_or_enum(attribute_json):
        return ""
    if not attribute_json["is_used"]:
        return ""
    label = attribute_json["label"]
    class_name = attribute_json["domain"]
    return '	get_map.emplace("cim:' + class_name + "." + label + '", &get_' + class_name + "_" + label + ");\n"


def insert_enum_get_fn(text: str, render: Callable[[str], str]) -> str:
    attribute_txt = render(text)
    attribute_json = eval(attribute_txt)
    if not attribute_json["is_enum_attribute"]:
        return ""
    label = attribute_json["label"]
    class_name = attribute_json["domain"]
    return '	get_map.emplace("cim:' + class_name + "." + label + '", &get_' + class_name + "_" + label + ");\n"


def create_nullptr_assigns(text: str, render: Callable[[str], str]) -> str:
    attributes_txt = render(text)
    if attributes_txt.strip() == "":
        return ""
    else:
        attributes_json = eval(attributes_txt)
        nullptr_init_string = ""
        for attribute in attributes_json:
            if attribute["is_class_attribute"]:
                nullptr_init_string += "LABEL(nullptr), ".replace("LABEL", attribute["label"])

    if len(nullptr_init_string) > 2:
        return " : " + nullptr_init_string[:-2]
    else:
        return ""


# These create_ functions are used to generate the implementations for
# the entries in the dynamic_switch maps referenced in assignments.cpp and Task.cpp
def create_class_assign(text: str, render: Callable[[str], str]) -> str:
    attribute_txt = render(text)
    attribute_json = eval(attribute_txt)
    assign = ""
    attribute_class = attribute_json["attribute_class"]
    if _attribute_is_primitive_or_datatype_or_enum(attribute_json):
        return ""
    if attribute_json["is_list_attribute"]:
        if "inverse_role" in attribute_json:
            inverse = attribute_json["inverse_role"].split(".")
            assign = (
                """
bool assign_INVERSEC_INVERSEL(BaseClass*, BaseClass*);
bool assign_OBJECT_CLASS_LABEL(BaseClass* BaseClass_ptr1, BaseClass* BaseClass_ptr2)
{
	OBJECT_CLASS* element = dynamic_cast<OBJECT_CLASS*>(BaseClass_ptr1);
	ATTRIBUTE_CLASS* element2 = dynamic_cast<ATTRIBUTE_CLASS*>(BaseClass_ptr2);
	if (element != nullptr && element2 != nullptr)
	{
		if (std::find(element->LABEL.begin(), element->LABEL.end(), element2) == element->LABEL.end())
		{
			element->LABEL.push_back(element2);
			return assign_INVERSEC_INVERSEL(BaseClass_ptr2, BaseClass_ptr1);
		}
		return true;
	}
	return false;
}""".replace(  # noqa: E101,W191
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
bool assign_OBJECT_CLASS_LABEL(BaseClass* BaseClass_ptr1, BaseClass* BaseClass_ptr2)
{
	if (OBJECT_CLASS* element = dynamic_cast<OBJECT_CLASS*>(BaseClass_ptr1))
	{
		if (dynamic_cast<ATTRIBUTE_CLASS*>(BaseClass_ptr2) != nullptr)
		{
			element->LABEL.push_back(dynamic_cast<ATTRIBUTE_CLASS*>(BaseClass_ptr2));
			return true;
		}
	}
	return false;
}""".replace(  # noqa: E101,W191
                    "OBJECT_CLASS", attribute_json["domain"]
                )
                .replace("ATTRIBUTE_CLASS", attribute_class)
                .replace("LABEL", attribute_json["label"])
            )
    elif "inverse_role" in attribute_json:
        inverse = attribute_json["inverse_role"].split(".")
        assign = (
            """
bool assign_INVERSEC_INVERSEL(BaseClass*, BaseClass*);
bool assign_OBJECT_CLASS_LABEL(BaseClass* BaseClass_ptr1, BaseClass* BaseClass_ptr2)
{
	OBJECT_CLASS* element = dynamic_cast<OBJECT_CLASS*>(BaseClass_ptr1);
	ATTRIBUTE_CLASS* element2 = dynamic_cast<ATTRIBUTE_CLASS*>(BaseClass_ptr2);
	if (element != nullptr && element2 != nullptr)
	{
		if (element->LABEL != element2)
		{
			element->LABEL = element2;
			return assign_INVERSEC_INVERSEL(BaseClass_ptr2, BaseClass_ptr1);
		}
		return true;
	}
	return false;
}""".replace(  # noqa: E101,W191
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
bool assign_OBJECT_CLASS_LABEL(BaseClass* BaseClass_ptr1, BaseClass* BaseClass_ptr2)
{
	if(OBJECT_CLASS* element = dynamic_cast<OBJECT_CLASS*>(BaseClass_ptr1))
	{
		element->LABEL = dynamic_cast<ATTRIBUTE_CLASS*>(BaseClass_ptr2);
		if (element->LABEL != nullptr)
		{
			return true;
		}
	}
	return false;
}""".replace(  # noqa: E101,W191
                "OBJECT_CLASS", attribute_json["domain"]
            )
            .replace("ATTRIBUTE_CLASS", attribute_class)
            .replace("LABEL", attribute_json["label"])
        )

    return assign


def create_assign(text: str, render: Callable[[str], str]) -> str:
    attribute_txt = render(text)
    attribute_json = eval(attribute_txt)
    assign = ""
    if not _attribute_is_primitive_or_datatype_or_enum(attribute_json):
        return ""

    if not _attribute_is_primitive_string(attribute_json):
        assign = (
            """
bool assign_CLASS_LABEL(std::stringstream &buffer, BaseClass* BaseClass_ptr1)
{
	if (CLASS* element = dynamic_cast<CLASS*>(BaseClass_ptr1))
	{
		buffer >> element->LBL_WO_KEYWORD;
		if (buffer.fail())
			return false;
		else
			return true;
	}
	return false;
}
""".replace(  # noqa: E101,W191
                "CLASS", attribute_json["domain"]
            )
            .replace("LABEL", attribute_json["label"])
            .replace("LBL_WO_KEYWORD", _get_label_without_keyword(attribute_json["label"]))
        )
    else:  # _attribute_is_primitive_string
        assign = """
bool assign_CLASS_LABEL(std::stringstream &buffer, BaseClass* BaseClass_ptr1)
{
	if (CLASS* element = dynamic_cast<CLASS*>(BaseClass_ptr1))
	{
		element->LABEL = buffer.str();
		if (buffer.fail())
			return false;
		else
			return true;
	}
	return false;
}
""".replace(  # noqa: E101,W191
            "CLASS", attribute_json["domain"]
        ).replace(
            "LABEL", attribute_json["label"]
        )

    return assign


def create_class_get(text: str, render: Callable[[str], str]) -> str:
    attribute_txt = render(text)
    attribute_json = eval(attribute_txt)
    if _attribute_is_primitive_or_datatype_or_enum(attribute_json):
        return ""
    if not attribute_json["is_used"]:
        return ""
    if attribute_json["is_list_attribute"]:
        get = """
bool get_OBJECT_CLASS_LABEL(const BaseClass* BaseClass_ptr1, std::list<const BaseClass*>& BaseClass_list)
{
	if (const OBJECT_CLASS* element = dynamic_cast<const OBJECT_CLASS*>(BaseClass_ptr1))
	{
		std::copy(element->LABEL.begin(), element->LABEL.end(), std::back_inserter(BaseClass_list));
		return !BaseClass_list.empty();
	}
	return false;
}
""".replace(  # noqa: E101,W191
            "OBJECT_CLASS", attribute_json["domain"]
        ).replace(
            "LABEL", attribute_json["label"]
        )
    else:
        get = """
bool get_OBJECT_CLASS_LABEL(const BaseClass* BaseClass_ptr1, std::list<const BaseClass*>& BaseClass_list)
{
	if (const OBJECT_CLASS* element = dynamic_cast<const OBJECT_CLASS*>(BaseClass_ptr1))
	{
		if (element->LABEL != 0)
		{
			BaseClass_list.push_back(element->LABEL);
			return true;
		}
	}
	return false;
}
""".replace(  # noqa: E101,W191
            "OBJECT_CLASS", attribute_json["domain"]
        ).replace(
            "LABEL", attribute_json["label"]
        )

    return get


def create_get(text: str, render: Callable[[str], str]) -> str:
    attribute_txt = render(text)
    attribute_json = eval(attribute_txt)
    get = ""
    if not _attribute_is_primitive_or_datatype(attribute_json):
        return ""

    get = (
        """
bool get_CLASS_LABEL(const BaseClass* BaseClass_ptr1, std::stringstream& buffer)
{
	if (const CLASS* element = dynamic_cast<const CLASS*>(BaseClass_ptr1))
	{
		buffer << element->LBL_WO_KEYWORD;
		if (!buffer.str().empty())
		{
			return true;
		}
	}
	buffer.setstate(std::ios::failbit);
	return false;
}
""".replace(  # noqa: E101,W191
            "CLASS", attribute_json["domain"]
        )
        .replace("LABEL", attribute_json["label"])
        .replace("LBL_WO_KEYWORD", _get_label_without_keyword(attribute_json["label"]))
    )

    return get


def create_enum_get(text: str, render: Callable[[str], str]) -> str:
    attribute_txt = render(text)
    attribute_json = eval(attribute_txt)
    if not attribute_json["is_enum_attribute"]:
        return ""

    get = """
bool get_CLASS_LABEL(const BaseClass* BaseClass_ptr1, std::stringstream& buffer)
{
	if (const CLASS* element = dynamic_cast<const CLASS*>(BaseClass_ptr1))
	{
		buffer << element->LABEL;
		if (!buffer.str().empty())
		{
			return true;
		}
	}
	buffer.setstate(std::ios::failbit);
	return false;
}
""".replace(  # noqa: E101,W191
        "CLASS", attribute_json["domain"]
    ).replace(
        "LABEL", attribute_json["label"]
    )

    return get


def attribute_decl(text: str, render: Callable[[str], str]) -> str:
    attribute_txt = render(text)
    attribute_json = eval(attribute_txt)
    return _attribute_decl(attribute_json)


def _attribute_decl(attribute: dict) -> str:
    _class = attribute["attribute_class"]
    if _attribute_is_primitive_or_datatype_or_enum(attribute):
        return "CIMPP::" + _class
    if attribute["is_list_attribute"]:
        return "std::list<CIMPP::" + _class + "*>"
    else:
        return "CIMPP::" + _class + "*"


def create_attribute_includes(text: str, render: Callable[[str], str]) -> str:
    unique = {}
    include_string = ""
    input_text = render(text)
    json_string = input_text.replace("'", '"')
    json_string_no_html_esc = json_string.replace("&quot;", '"')
    if json_string_no_html_esc:
        attributes = json.loads(json_string_no_html_esc)
        for attribute in attributes:
            if _attribute_is_primitive_or_datatype_or_enum(attribute):
                unique[attribute["attribute_class"]] = True
    for clarse in sorted(unique):
        include_string += '#include "' + clarse + '.hpp"\n'
    return include_string


def create_attribute_class_declarations(text: str, render: Callable[[str], str]) -> str:
    unique = {}
    include_string = ""
    input_text = render(text)
    json_string = input_text.replace("'", '"')
    json_string_no_html_esc = json_string.replace("&quot;", '"')
    if json_string_no_html_esc:
        attributes = json.loads(json_string_no_html_esc)
        for attribute in attributes:
            if attribute["is_class_attribute"] or attribute["is_list_attribute"]:
                unique[attribute["attribute_class"]] = True
    for clarse in sorted(unique):
        include_string += "	class " + clarse + ";\n"
    return include_string


def set_default(text: str, render: Callable[[str], str]) -> str:
    result = render(text)
    return _set_default(result)


def _set_default(datatype: str) -> str:
    # the field {{datatype}} either contains the multiplicity of an attribute if it is a reference or otherwise the
    # datatype of the attribute. If no datatype is set and there is also no multiplicity entry for an attribute, the
    # default value is set to None. The multiplicity is set for all attributes, but the datatype is only set for basic
    # data types. If the data type entry for an attribute is missing, the attribute contains a reference and therefore
    # the default value is either None or [] depending on the multiplicity. See also _write_files in cimgen.py.
    if datatype in ["M:1", "M:0..1", "M:1..1", "M:0..n", "M:1..n", ""] or "M:" in datatype:
        return "0"
    datatype = datatype.split("#")[1]
    if datatype in ["integer", "Integer"]:
        return "0"
    elif datatype in ["String", "DateTime", "Date"]:
        return "''"
    elif datatype == "Boolean":
        return "false"
    elif datatype == "Float":
        return "0.0"
    else:
        return "nullptr"


def _attribute_is_primitive_or_datatype_or_enum(attribute: dict) -> bool:
    return _attribute_is_primitive_or_datatype(attribute) or attribute["is_enum_attribute"]


def _attribute_is_primitive_or_datatype(attribute: dict) -> bool:
    return attribute["is_primitive_attribute"] or attribute["is_datatype_attribute"]


def _attribute_is_primitive_string(attribute: dict) -> bool:
    return attribute["is_primitive_attribute"] and (
        attribute["attribute_class"] not in ("Float", "Decimal", "Integer", "Boolean")
    )


# The code below this line is used after the main cim_generate phase to generate
# two include files. They are called CIMClassList.hpp and IEC61970.hpp, and
# contain the list of the class files and the list of define functions that add
# the generated functions into the function tables.

class_blacklist = [
    "assignments",
    "BaseClass",
    "BaseClassDefiner",
    "CGMESProfile",
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


def _is_primitive_or_enum_class(file: Path) -> bool:
    with file.open(encoding="utf-8") as f:
        try:
            for line in f:
                if "static const BaseClassDefiner declare();" in line:
                    return False
        except UnicodeDecodeError as error:
            print("Warning: UnicodeDecodeError parsing {0}: {1}".format(file.name, error))
    return True


def _create_header_include_file(
    directory: Path,
    header_include_filename: str,
    header: list[str],
    footer: list[str],
    before: str,
    after: str,
    blacklist: list[str],
) -> None:
    lines = []
    for file in sorted(directory.glob("*.hpp"), key=lambda f: f.stem):
        basename = file.stem
        if not _is_primitive_or_enum_class(file) and basename not in blacklist:
            lines.append(before + basename + after)
    for line in lines:
        header.append(line)
    for line in footer:
        header.append(line)
    header_include_filepath = directory / header_include_filename
    with header_include_filepath.open("w", encoding="utf-8") as f:
        f.writelines(header)


def resolve_headers(path: str, version: str) -> None:  # NOSONAR
    class_list_header = [
        "#ifndef CIMCLASSLIST_H\n",
        "#define CIMCLASSLIST_H\n",
        "/*\n",
        "Generated from the CGMES files via cimgen: https://github.com/sogno-platform/cimgen\n",
        "*/\n",
        "#include <list>\n",
        '#include "IEC61970.hpp"\n',
        "using namespace CIMPP;\n",
        "static std::list<BaseClassDefiner> CIMClassList =\n",
        "{\n",
    ]
    class_list_footer = [
        "	UnknownType::declare(),\n",
        "};\n",
        "#endif // CIMCLASSLIST_H\n",
    ]

    _create_header_include_file(
        Path(path),
        "CIMClassList.hpp",
        class_list_header,
        class_list_footer,
        "	",
        "::declare(),\n",
        class_blacklist,
    )

    iec61970_header = [
        "#ifndef IEC61970_H\n",
        "#define IEC61970_H\n",
        "/*\n",
        "Generated from the CGMES files via cimgen: https://github.com/sogno-platform/cimgen\n",
        "*/\n",
        "\n",
    ]
    iec61970_footer = [
        '#include "UnknownType.hpp"\n',
        "#endif",
    ]

    _create_header_include_file(
        Path(path),
        "IEC61970.hpp",
        iec61970_header,
        iec61970_footer,
        '#include "',
        '.hpp"\n',
        iec61970_blacklist,
    )
