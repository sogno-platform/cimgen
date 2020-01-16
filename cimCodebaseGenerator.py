import os
import xmltodict
import chevron
from time import time
import json

import logging

logger = logging.getLogger(__name__)

# The definitions are often contained within a string with a name
# such as "$rdf:about" or "$rdf:resource", this extracts the
# useful bit
def _get_about_or_resource(object_dic):
    if '$rdf:resource' in object_dic:
        return object_dic['$rdf:resource']
    elif '$rdf:about' in object_dic:
        return object_dic['$rdf:about']
    elif 'rdfs:Literal' in object_dic:
        return object_dic['rdfs:Literal']
    return object_dic


# Extracts the text out of the dictionary after xmltodict, text is labeled by key '_'
def _extract_text(object_dic):
    if isinstance(object_dic, list):
        return object_dic[0]['_']
    elif '_' in object_dic.keys():
        return object_dic['_']
    else:
        return ""


# Extract String out of list or dictionary
def _extract_string(object_dic):
    if isinstance(object_dic, list):
        if len(object_dic) > 0:
            if type(object_dic[0]) == 'string' or isinstance(object_dic[0], str):
                return object_dic[0]
            return _get_about_or_resource(object_dic[0])
    return _get_about_or_resource(object_dic)


# Add a new class into a profile
def _new_class(profile, class_name, object_dic):
    if not (class_name in profile):
        profile[class_name] = object_dic or {}
        profile[class_name]['attributes'] = []
    else:
        logger.info("Class {} already exists".format(class_name))
    return profile

# Some names are encoded as #name or http://some-url#name
# This function returns the name
def _get_rid_of_hash(name):
    tokens = name.split('#')
    if len(tokens) == 1:
        return tokens[0]
    if len(tokens) > 1:
        return tokens[1]
    return name

# Set an attribute for an object
def _set_attr(object_dic, key, value):
    object_dic[key] = value
    return object_dic

def _parse_rdf(input_dic):
    classes_map = {}
    package_name = []
    attributes = []

    # Generates list with dictionaries as elements
    descriptions = input_dic['rdf:RDF']['rdf:Description']

    # Iterate over list elements
    for list_elem in descriptions:
        object_dic = {}

        if list_elem is not None:
            object_dic = _set_attr(object_dic, 'about', _get_rid_of_hash(_extract_string(list_elem['$rdf:about'])))

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
                    text = _extract_text(list_elem[key]).replace('–', '-').replace('“', '"')\
                        .replace('”', '"').replace('’', "'").replace('°', '').replace('\n', ' ')
                    object_dic = _set_attr(object_dic, name[1], text)
                elif name[1] in ['domain', 'subClassOf', 'belongsToCategory', 'multiplicity']:
                    object_dic = _set_attr(object_dic, name[1], _get_rid_of_hash(_extract_string(list_elem[key])))
                else:

                    object_dic = _set_attr(object_dic, name[1], _extract_string(list_elem[key]))

        if 'type' in object_dic.keys():
            if object_dic['type'] == 'http://www.w3.org/2000/01/rdf-schema#Class':
                # Class
                classes_map = _new_class(classes_map, object_dic['label'], object_dic)
            elif object_dic['type'] == "http://www.w3.org/1999/02/22-rdf-syntax-ns#Property":
                # Property -> Attribute
                attributes.append(object_dic)

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
            logger.info("Class {} for attribute {} not found.".format(clarse, attribute))

    return {package_name[0]: classes_map}


# This function extracts all information needed for the creation of the python class files like the comments or the
# class name. After the extraction the function write_files is called to write the files with the template engine
# chevron
def _write_python_files(elem_dict, version, langPack):

    # Iterate over Classes
    for class_name in elem_dict.keys():
        sub_class_of = None

        # extract attributes
        attributes_array = _find_multiple_attributes(elem_dict[class_name]['attributes'])

        class_location = None

        # Check if the current class has a parent class
        if 'subClassOf' in elem_dict[class_name].keys():
            sub_class_of = elem_dict[class_name]['subClassOf']

            if sub_class_of not in elem_dict.keys():
                logger.info("Parent class {} for class {} not found".format(sub_class_of, class_name))
                continue
            else:
                class_location = 'cimpy.' + version + "." + sub_class_of

        # extract comments
        if 'comment' in elem_dict[class_name].keys():
            comment = elem_dict[class_name]['comment']
        else:
            comment = ""

        _write_files(class_name, attributes_array, elem_dict[class_name]['class_origin'],
                     class_location, sub_class_of, comment, version, langPack)


def _create_init(path):
    init_file = path + "/__init__.py"
    with open(init_file, 'w'):
        pass


# creates the Base class file, all classes inherit from this class
def _create_base(path):
    base_path = path + "/Base.py"
    base = ['from enum import Enum\n\n', '\n', 'class Base():\n', '    """\n', '    Base Class for CIM\n',
            '    """\n\n',
            '    cgmesProfile = Enum("cgmesProfile", {"EQ": 0, "SSH": 1, "TP": 2, "SV": 3, "DY": 4, "GL": 5, "DI": 6})',
            '\n\n', '    def __init__(self, *args, **kw_args):\n', '        pass\n',
            '\n', '    def printxml(self, dict={}):\n', '        return dict\n']

    with open(base_path, 'w') as f:
        for line in base:
            f.write(line)


def _write_files(class_name, attributes_array, class_origin, class_location,
                 sub_class_of, comment, version, langPack):

    version_path = os.path.join(os.getcwd(), version)
    if not os.path.exists(version_path):
        os.makedirs(version_path)
        _create_init(version_path)
        _create_base(version_path)

    class_file = os.path.join(version_path, class_name + ".py")

    if sub_class_of is None:
        # If class has no subClassOf key it is a subclass of the Base class
        sub_class_of = "Base"
        class_location = "cimpy." + version + ".Base"
        super_init = False
    else:
        # If class is a subclass a super().__init__() is needed
        super_init = True

    # The entry dataType for an attribute is only set for basic data types. If the entry is not set here, the attribute
    # is a reference to another class and therefore the entry dataType is generated and set to the multiplicity
    for i in range(len(attributes_array)):
        if 'dataType' not in attributes_array[i].keys() and 'multiplicity' in attributes_array[i].keys():
            attributes_array[i]['dataType'] = attributes_array[i]['multiplicity']

    template_files = langPack.template_files
    partials = langPack.partials

    for template_info in template_files:
        class_file = os.path.join(version_path, class_name + template_info["ext"])
        if not os.path.exists(class_file):
            with open(class_file, 'w') as file:

                with open(template_info["filename"]) as f:
                    args = {
                        'data': {
                            "class_name": class_name, "attributes": attributes_array,
                            "class_origin": class_origin, "subClassOf": sub_class_of,
                            "ClassLocation": class_location, "super_init": super_init,
                            "class_comment": comment, "langPack": langPack,
                        },
                        'template': f,
                        'partials_dict': partials
                    }
                    output = chevron.render(**args)
                file.write(output)
        else:
            logger.info("Class file for class {} already exists.".format(class_file))


# Find multiple entries for the same attribute
def _find_multiple_attributes(attributes_array):
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


# If multiple CGMES schema files for one profile are read, e.g. Equipment Core and Equipment Core Short Circuit
# this function merges these into one profile, e.g. Equipment, after this function only one dictionary entry for each
# profile exists. The profiles_array contains one entry for each CGMES schema file which was read.
def _merge_profiles(profiles_array):
    profiles_dict = {}
    # Iterate through array elements
    for elem_dict in profiles_array:
        # Iterate over profile names
        for profile_key in elem_dict.keys():
            if profile_key in profiles_dict.keys():
                # Iterate over classes and check for multiple class definitions
                for class_key in elem_dict[profile_key]:
                    if class_key in profiles_dict[profile_key].keys():
                        # If class allready exists in packageDict add attributes to attributes array
                        if len(elem_dict[profile_key][class_key]['attributes']) > 0:
                            attributes_package = profiles_dict[profile_key][class_key]['attributes']
                            attributes_array = elem_dict[profile_key][class_key]['attributes']
                            profiles_dict[profile_key][class_key]['attributes'] = attributes_package + attributes_array
                    # If class is not in packageDict, create entry
                    else:
                        profiles_dict[profile_key][class_key] = elem_dict[profile_key][class_key]
            # If package name not in packageDict create entry
            else:
                profiles_dict[profile_key] = elem_dict[profile_key]
    return profiles_dict


# This function merges the classes defined in all profiles into one class with all attributes defined in any profile.
# The origin of the class definitions and the origin of the attributes of a class are tracked and used to generate
# the possibleProfileList used for the serialization.
def _merge_classes(profiles_dict):
    class_dict = {}

    # Iterate over profiles
    for package_key in profiles_dict.keys():
        # get short name of the profile
        short_name = short_package_name[package_key]
        # iterate over classes in the current profile
        for class_key in profiles_dict[package_key]:
            # class already defined?
            if class_key not in class_dict.keys():
                # store class and class origin
                class_dict[class_key] = profiles_dict[package_key][class_key]
                class_dict[class_key]['class_origin'] = [{'origin': short_name}]
                for attr in class_dict[class_key]['attributes']:
                    # store origin of the attributes
                    attr['attr_origin'] = [{'origin': short_package_name[package_key]}]
            else:
                # some inheritance information is stored only in one of the packages. Therefore it has to be checked
                # if the subClassOf attribute is set. See for example TopologicalNode definitions in SV and TP.
                if 'subClassOf' not in class_dict[class_key].keys():
                    if 'subClassOf' in profiles_dict[package_key][class_key].keys():
                        class_dict[class_key]['subClassOf'] = profiles_dict[package_key][class_key]['subClassOf']

                # check if profile is already stored in class origin list
                for origin in class_dict[class_key]['class_origin']:
                    multiple_origin = False
                    if short_name == origin['origin']:
                        # origin already stored
                        multiple_origin = True
                        break
                if not multiple_origin:
                    class_dict[class_key]['class_origin'].append({'origin': short_name})

                for attr in profiles_dict[package_key][class_key]['attributes']:
                    # check if attribute is already in attributes list
                    multiple_attr = False
                    for attr_set in class_dict[class_key]['attributes']:
                        if attr['label'] == attr_set['label']:
                            # attribute already in attributes list, check if origin is new
                            multiple_attr = True
                            for origin in attr_set['attr_origin']:
                                multiple_attr_origin = False
                                if origin['origin'] == short_name:
                                    multiple_attr_origin = True
                                    break
                            if not multiple_attr_origin:
                                # new origin
                                attr_set['attr_origin'].append({'origin': short_name})
                            break
                    if not multiple_attr:
                        # new attribute
                        attr['attr_origin'] = [{'origin': short_name}]
                        class_dict[class_key]['attributes'].append(attr)
    return class_dict

def cim_generate(directory, version, langPack):
    """Generates cgmes python classes from cgmes ontology

    This function uses package xmltodict to parse the RDF files. The parse_rdf function sorts the classes to
    the corresponding packages. Since multiple files can be read, e.g. Equipment Core and Equipment Short Circuit, the
    classes of these profiles are merged into one profile with the merge_profiles function. After that the merge_classes
    function merges classes defined in multiple profiles into one class and tracks the origin of the class and their
    attributes. This information is stored in the class variable possibleProfileList and used for serialization.
    For more information see the cimexport function in the cimpy package. Finally the
    write_python_files function extracts all information needed for the creation of the python files and creates them
    with the template engine chevron. The attribute version of this function defines the name of the folder where the
    created classes are stored. This folder should not exist and is created in the class generation procedure.

    :param directory: path to RDF files containing cgmes ontology, e.g. directory = "./examples/cgmes_schema/cgmes_v2_4_15_schema"
    :param version: CGMES version, e.g. version = "cgmes_v2_4_15"
    """
    cwd = os.getcwd()
    os.chdir(os.path.dirname(__file__))
    profiles_array = []

    t0 = time()

    # iterate over files in the directory and check if they are RDF files
    for file in os.listdir(directory):
        if file.endswith(".rdf"):
            logger.info('Start of parsing file \"%s\"', file)

            file_path = os.path.join(directory, file)
            xmlstring = open(file_path, encoding="utf8").read()

            # parse RDF files and create a dictionary from the RDF file
            parse_result = xmltodict.parse(xmlstring, attr_prefix="$", cdata_key="_", dict_constructor=dict)
            parsed = _parse_rdf(parse_result)
            profiles_array.append(parsed)

    # merge multiple profile definitions into one profile
    profiles_dict = _merge_profiles(profiles_array)

    # merge classes from different profiles into one class and track origin of the classes and their attributes
    class_dict_with_origins = _merge_classes(profiles_dict)

    # get information for writing python files and write python files
    _write_python_files(class_dict_with_origins, version, langPack)

    os.chdir(cwd)

    logger.info('Elapsed Time: {}s\n\n'.format(time() - t0))


# used to map the profile name to their abbreviations according to the CGMES standard
short_package_name = {
    "DiagramLayoutVersion": 'DI',
    "DynamicsVersion": "DY",
    "EquipmentVersion": "EQ",
    "GeographicalLocationVersion": "GL",
    "StateVariablesVersion": "SV",
    "SteadyStateHypothesisVersion": "SSH",
    "TopologyVersion": "TP"
}
