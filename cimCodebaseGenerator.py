import os
import xmltodict
import chevron


# called by chevron, text contains the label {{dataType}}, which is evaluated by the renderer (see class template)
def set_default(text, render):
    result = render(text)

    # the field {{dataType}} either contains the multiplicity of an attribute if it is a reference or otherwise the
    # datatype of the attribute. If no datatype is set and there is also no multiplicity entry for an attribute, the
    # default value is set to None. The multiplicity is set for all attributes, but the datatype is only set for basic
    # data types. If the data type entry for an attribute is missing, the attribute contains a reference and therefore
    # the default value is either None or [] depending on the mutliplicity. See also write_python_files
    if result in ['M:1', 'M:0..1', 'M:1..1', '']:
        return 'None'
    elif result in ['M:0..n', 'M:1..n'] or 'M:' in result:
        return '[]'

    result = result.split('#')[1]
    if result in ['integer', 'Integer']:
        return '0'
    elif result in ['String', 'DateTime', 'Date']:
        return "''"
    elif result == 'Boolean':
        return 'False'
    else:
        # everything else should be a float
        return '0.0'


# The definitions are often contained within a string with a name
# such as "$rdf:about" or "$rdf:resource", this extracts the
# useful bit
def get_about_or_resource(object_dic):
    if '$rdf:resource' in object_dic:
        return object_dic['$rdf:resource']
    elif '$rdf:about' in object_dic:
        return object_dic['$rdf:about']
    elif 'rdfs:Literal' in object_dic:
        return object_dic['rdfs:Literal']
    return object_dic


def extract_text(object_dic):
    if isinstance(object_dic, list):
        return object_dic[0]['_']
    elif '_' in object_dic.keys():
        return object_dic['_']
    else:
        return ""


# Extract String out of list or dictionary
def extract_string(object_dic):
    if isinstance(object_dic, list):
        if len(object_dic) > 0:
            if type(object_dic[0]) == 'string' or isinstance(object_dic[0], str):
                return object_dic[0]
            return get_about_or_resource(object_dic[0])
    return get_about_or_resource(object_dic)


# Add a new class into a profile
def new_class(profile, class_name, object_dic):
    if not (class_name in profile):
        profile[class_name] = object_dic or {}
        profile[class_name]['attributes'] = []
    else:
        console.error("Class already exists.")
    return profile


# Some names are encoded as #name or http://some-url#name
# This function returns the name
def get_rid_of_hash(name):
    tokens = name.split('#')
    if len(tokens) == 1:
        return tokens[0]
    if len(tokens) > 1:
        return tokens[1]
    return name


# Set an attribute for an object
def set_attr(object_dic, key, value):
    object_dic[key] = value
    return object_dic


def parse_rdf(input_dic):
    classes_map = {}
    package_name = []
    attributes = []
    # packages = []

    # Generates list with dictionaries as elements
    descriptions = input_dic['rdf:RDF']['rdf:Description']

    # Iterate over list elements
    for list_elem in descriptions:
        object_dic = {}

        if list_elem is not None:
            object_dic = set_attr(object_dic, 'about', get_rid_of_hash(extract_string(list_elem['$rdf:about'])))

        # Iterate over possible keys and set attribute for object if defined
        keys = ['cims:dataType', 'rdfs:domain', 'rdfs:label', 'rdfs:range', 'rdfs:subClassOf',
                'cims:stereotype', 'rdf:type', 'cims:isFixed', 'cims:belongsToCategory',
                'rdfs:comment', 'cims:multiplicity']

        for key in keys:
            # Is key defined?
            if key in list_elem.keys():
                name = key.split(':')
                if keys == 'rdfs:domain' and list_elem['rdfs:domain'] is None:
                    continue
                if name[1] in ['label', 'comment']:
                    # Label text marked with '_'
                    text = extract_text(list_elem[key]).replace('–', '-').replace('“', '"')\
                        .replace('”', '"').replace('’', "'").replace('°', '').replace('\n', ' ')
                    object_dic = set_attr(object_dic, name[1], text)
                elif name[1] in ['domain', 'subClassOf', 'belongsToCategory', 'multiplicity']:
                    object_dic = set_attr(object_dic, name[1], get_rid_of_hash(extract_string(list_elem[key])))
                else:

                    object_dic = set_attr(object_dic, name[1], extract_string(list_elem[key]))

        if 'type' in object_dic.keys():
            if object_dic['type'] == 'http://www.w3.org/2000/01/rdf-schema#Class':
                # Class
                classes_map = new_class(classes_map, object_dic['label'], object_dic)
            elif object_dic['type'] == "http://www.w3.org/1999/02/22-rdf-syntax-ns#Property":
                # Property -> Attribute
                attributes.append(object_dic)
            # not for CGMES-Standard, only for CIM-Standard
            # elif object_dic['type'] == "http://iec.ch/TC57/1999/rdf-schema-extensions-19990926#ClassCategory":
            #     # Class Category -> Package Name
            #     packages.append(object_dic['about'])

        # only for CGMES-Standard
        if 'stereotype' in object_dic.keys():
            if object_dic['stereotype'] == 'Entsoe':  # entsoe in object_dic
                # Record the type, which will be [PackageName]Version
                package_name.append(object_dic['about'])

    # Add attributes to corresponding class
    for attribute in attributes:
        clarse = attribute['domain']
        if clarse and classes_map[clarse]:
            classes_map[clarse]['attributes'].append(attribute)
        else:
            console.error("Class somewhere else: ", attribute)

    # only for CIM-Standard
    # parsed_map = {}
    # for elem in packages:
    #     parsed_map[elem] = {}
    #
    # not_btc = {}
    #
    # # Add classes to corresponding packages
    # for key in profile_data.keys():
    #     if 'belongsToCategory' in profile_data[key].keys():
    #         cat = profile_data[key]['belongsToCategory']
    #         if cat in packages:
    #             parsed_map[cat][key] = profile_data[key]
    #         else:
    #             parsed_map[cat] = {}
    #             parsed_map[cat][key] = profile_data[key]
    #     else:
    #         # Catch elements without belongsToCategory, should be empty
    #         not_btc[key] = profile_data[key]
    #
    # return parsed_map, not_btc

    return {package_name[0]: classes_map}


def process_array_of_category_maps(elem_dict, version):
    no_parent_found = []
    # Iterate over Classes
    package_name = ""

    for class_name in elem_dict.keys():
        sub_class_of = None

        attributes_array = find_multiple_attributes(elem_dict[class_name]['attributes'])

        # ToDo: used?
        class_location = None

        # Check if the current class has a parent class
        if 'subClassOf' in elem_dict[class_name].keys():
            sub_class_of = elem_dict[class_name]['subClassOf']

            # ToDo: all classes in one folder or subfolders for CIM structure?
            package_name = ""
            # If class has a parent class find the package name (location) of the parent class
            # sub_package = find_parent_class_package(sub_class_of, package_name, elem_dict)
            if sub_class_of not in elem_dict.keys():
                no_parent_found.append(elem_dict[class_name])
                continue
            else:
                class_location = 'cimpy.' + version + "." + sub_class_of
        if 'comment' in elem_dict[class_name].keys():
            comment = elem_dict[class_name]['comment']
        else:
            comment = ""

        write_python_files(package_name, class_name, attributes_array, elem_dict[class_name]['class_origin'],
                           class_location, sub_class_of, comment, version)
    return no_parent_found


def create_init(path):
    init_file = path + "/__init__.py"
    with open(init_file, 'w'):
        pass


def create_base(path):
    base_path = path + "/Base.py"
    base = ["class Base():\n", '    """\n', '    Base Class for CIM\n',
            '    """\n', '    def __init__(self, *args, **kw_args):\n', '        pass',
            '\n', '    def printxml(self, dict={}):\n', '        return dict\n']
    with open(base_path, 'w') as f:
        for line in base:
            f.write(line)


def write_python_files(package_name, class_name, attributes_array, class_origin, class_location,
                       sub_class_of, comment, version):
    version_path = "./" + version
    if not os.path.exists(version_path):
        os.makedirs(version_path)
        create_init(version_path)
        create_base(version_path)

    # only for CIM-Standard
    # package = package_name.split('_')[1]

    # only for CGMES-Standard
    # ToDo: usage
    # package = package_name.split('Version')[0]
    # path = "./" + version + '/' + package

    # ToDo: only use if classes in subfolders like CGMES or CIM structure
    # Check if package folder exists
    # if not os.path.exists(path):
    #     os.makedirs(path)
    #     # Creates init file in package directory
    #     create_init(path)

    class_file = version_path + "/" + class_name + ".py"

    # If class is a subclass a super().__init__() is needed
    super_init = True

    # If class has no subClassOf key it is a subclass of the Base class
    if sub_class_of is None:
        sub_class_of = "Base"
        class_location = "cimpy." + version + ".Base"
        super_init = False

    # The entry dataType for an attribute is only set for basic data types. If the entry is not set here, the attribute
    # is a reference to another class and therefore the entry dataType is generated and set to the multiplicity
    for i in range(len(attributes_array)):
        if 'dataType' not in attributes_array[i].keys() and 'multiplicity' in attributes_array[i].keys():
            attributes_array[i]['dataType'] = attributes_array[i]['multiplicity']

    if not os.path.exists(class_file):
        with open(class_file, 'w') as file:

            with open('cimpy_class_template.mustache') as f:
                output = chevron.render(f, {"class_name": class_name, "attributes": attributes_array,
                                            "class_origin": class_origin,
                                            "setDefault": set_default, "subClassOf": sub_class_of,
                                            "ClassLocation": class_location, "super_init": super_init,
                                            "class_comment": comment,
                                            })
            file.write(output)
    else:
        pass


# Checks if parent Class exists and returns the package name of the parent class
def find_parent_class_package(parent_class, package_name, elem_dict):
    # first look for the parent class in the same package as the subclass
    if parent_class in elem_dict[package_name].keys():
        # only for CGMES-Standard
        return package_name.split('Version')[0]

    for package_name in elem_dict.keys():
        if parent_class in elem_dict[package_name].keys():
            # only for CIM-Standard
            # return package_name.split('_')[1]

            # only for CGMES-Standard
            return package_name.split('Version')[0]
    return False


# Find multiple entries for the same attribute
def find_multiple_attributes(attributes_array):
    merged_attributes = []
    for elem in attributes_array:
        found = False
        for i in range(len(merged_attributes)):
            if elem['label'] == merged_attributes[i]['label']:
                found = True
                break
        if found is False:
            merged_attributes.append(elem)
    return merged_attributes


# ToDo: track class heritage, attributes heritage
# ToDo: change name? maybe create_package_dict
# Merges the attributes of the same classes and creates one dictionary out of the categoriesArray
def merge_classes(categories_array):
    package_dict = {}
    # Iterate through array elements
    for elem_dict in categories_array:
        # Iterate over package names
        for package_key in elem_dict.keys():
            if package_key in package_dict.keys():
                # Iterate over classes and check for multiple class definitions
                for class_key in elem_dict[package_key]:
                    if class_key in package_dict[package_key].keys():
                        # If class allready exists in packageDict add attributes to attributes array
                        if len(elem_dict[package_key][class_key]['attributes']) > 0:
                            attributes_package = package_dict[package_key][class_key]['attributes']
                            attributes_array = elem_dict[package_key][class_key]['attributes']
                            package_dict[package_key][class_key]['attributes'] = attributes_package + attributes_array
                    # If class is not in packageDict, create entry
                    else:
                        package_dict[package_key][class_key] = elem_dict[package_key][class_key]
            # If package name not in packageDict create entry
            else:
                package_dict[package_key] = elem_dict[package_key]
    package_dict = merge_classes_in_equipment(package_dict)
    return package_dict


# ToDo: Delete/modify
# ToDo: rename: create_class_dict
# Merges multiple class definitions into the Equipment package. The origin of all attributes defined outside
# of the Equipment schema are stored in the referenece dict
def merge_classes_in_equipment(package_dict):
    class_dict = {}
    for package_key in package_dict.keys():
        short_name = short_package_name[package_key]
        for class_key in package_dict[package_key]:
            if class_key not in class_dict.keys():
                class_dict[class_key] = package_dict[package_key][class_key]
                class_dict[class_key]['class_origin'] = [{'origin': short_name}]
                for attr in class_dict[class_key]['attributes']:
                    attr['attr_origin'] = [{'origin': short_package_name[package_key]}]
            else:
                for origin in class_dict[class_key]['class_origin']:
                    multiple_origin = False
                    if short_name == origin['origin']:
                        multiple_origin = True
                        break
                if not multiple_origin:
                    class_dict[class_key]['class_origin'].append({'origin': short_name})

                for attr in package_dict[package_key][class_key]['attributes']:
                    multiple_attr = False
                    for attr_set in class_dict[class_key]['attributes']:
                        if attr['label'] == attr_set['label']:
                            multiple_attr = True
                            for origin in attr_set['attr_origin']:
                                multiple_attr_origin = False
                                if origin['origin'] == short_name:
                                    multiple_attr_origin = True
                                    break
                            if not multiple_attr_origin:
                                attr_set['attr_origin'].append({'origin': short_name})
                            break
                    if not multiple_attr:
                        attr['attr_origin'] = [{'origin': short_name}]
                        class_dict[class_key]['attributes'].append(attr)

    return class_dict


def cim_generate(directory, version):
    """Generates cgmes python classes from cgmes ontology

    This function uses package xmltodict to parse the RDF files. The parse_rdf function sorts the classes to
    the corresponding packages. Since there can be multiple occurences of a class with different attributes in a package,
    the merge_classes function merges these into one class containing all attributes. Since multiple definitions of
    classes occur in different cgmes packages, all classes are merged into the Equipment package. For attributes defined
    outside the Equipment package, the reference_dict stores the origin of those. This dictionary is used for the export
    of the cgmes python classes. For more information see the cimexport function in the cimgen package. Finally the
    process_array_of_category_maps function modifies the classes and creates the python files using the template engine
    chevron.

    :param directory: path to RDF files containing cgmes ontology, e.g. directory = "./examples/cgmes_schema/cgmes_v2_4_15_schema"
    :param version: cgmes version, e.g. version = "cimgen_v2_4_15"
    """
    cwd = os.getcwd()
    os.chdir(os.path.dirname(__file__))
    categories_array = []
    # not_btc_array = []

    for file in os.listdir(directory):
        if file.endswith(".rdf"):
            file_path = directory + "/" + file
            xmlstring = open(file_path, encoding="utf8").read()

        parse_result = xmltodict.parse(xmlstring, attr_prefix="$", cdata_key="_", dict_constructor=dict)

        # only for CIM-Standard, not for CGMES-Standard
        # parsed, not_btc = parse_rdf(parse_result)
        # not_btc_array.append(not_btc)

        parsed = parse_rdf(parse_result)
        categories_array.append(parsed)

    package_dict = merge_classes(categories_array)
    no_parent_found = process_array_of_category_maps(package_dict, version)
    print("No Parent Class found for: ")
    for elem in no_parent_found:
        print("Class Name: ", elem['label'], " Parent Class Name: ", elem['subClassOf'])

    os.chdir(cwd)


short_package_name = {
    "DiagramLayoutVersion": 'DI',
    "DynamicsVersion": "DY",
    "EquipmentVersion": "EQ",
    "GeographicalLocationVersion": "GL",
    "StateVariablesVersion": "SV",
    "SteadyStateHypothesisVersion": "SSH",
    "TopologyVersion": "TP"
}