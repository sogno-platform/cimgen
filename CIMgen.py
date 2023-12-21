import html
import json
import logging
import os
import textwrap
from time import time

import xmltodict
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class RDFSEntry:
    def __init__(self, jsonObject):
        self.jsonDefinition = jsonObject
        return

    def asJson(self):
        jsonObject = {}
        if self.about() != None:
            jsonObject['about'] = self.about()
        if self.comment() != None:
            jsonObject['comment'] = self.comment()
        if self.dataType() != None:
            jsonObject['dataType'] = self.dataType()
        if self.domain() != None:
            jsonObject['domain'] = self.domain()
        if self.fixed() != None:
            jsonObject['isFixed'] = self.fixed()
        if self.label() != None:
            jsonObject['label'] = self.label()
        if self.multiplicity() != None:
            jsonObject['multiplicity'] = self.multiplicity()
        if self.range() != None:
            jsonObject['range'] = self.range()
        if self.stereotype() != None:
            jsonObject['stereotype'] = self.stereotype()
        if self.type() != None:
            jsonObject['type'] = self.type()
        if self.subClassOf() != None:
            jsonObject['subClassOf'] = self.subClassOf()
        if self.inverseRole() != None:
            jsonObject['inverseRole'] = self.inverseRole()
        if self.associationUsed() != None:
            jsonObject['associationUsed'] = self.associationUsed()
        jsonObject["isAssociationUsed"] = self.isAssociationUsed()
        return jsonObject

    def about(self):
        if '$rdf:about' in self.jsonDefinition:
            return RDFSEntry._get_rid_of_hash(RDFSEntry._get_about_or_resource(self.jsonDefinition['$rdf:about']))
        else:
            return None

    def associationUsed(self):
        if 'cims:AssociationUsed' in self.jsonDefinition:
            return RDFSEntry._extract_string(self.jsonDefinition['cims:AssociationUsed'])
        else:
            return None

    def isAssociationUsed(self) -> bool:
        if "cims:AssociationUsed" in self.jsonDefinition:
            return "yes" == RDFSEntry._extract_string(self.jsonDefinition["cims:AssociationUsed"]).lower()
        else:
            return True

    def comment(self):
        if 'rdfs:comment' in self.jsonDefinition:
            return RDFSEntry._extract_text(self.jsonDefinition['rdfs:comment']).replace('–', '-').replace('“', '"')\
                        .replace('”', '"').replace('’', "'").replace('°', '[SYMBOL REMOVED]').replace('º', '[SYMBOL REMOVED]').replace('\n', ' ')
        else:
            return None

    def dataType(self):
        if 'cims:dataType' in self.jsonDefinition:
            return RDFSEntry._extract_string(self.jsonDefinition['cims:dataType'])
        else:
            return None

    def domain(self):
        if 'rdfs:domain' in self.jsonDefinition:
            return RDFSEntry._get_rid_of_hash(RDFSEntry._extract_string(self.jsonDefinition['rdfs:domain']))
        else:
            return None

    def fixed(self):
        if 'cims:isFixed' in self.jsonDefinition:
            return RDFSEntry._extract_text(self.jsonDefinition['cims:isFixed'])
        else:
            return None

    def keyword(self):
        if "dcat:keyword" in self.jsonDefinition:
            return self.jsonDefinition["dcat:keyword"]
        else:
            return None

    def title(self):
        if "dct:title" in self.jsonDefinition:
            return RDFSEntry._extract_text(self.jsonDefinition["dct:title"])
        else:
            return None

    def inverseRole(self):
        if 'cims:inverseRoleName' in self.jsonDefinition:
            return RDFSEntry._get_rid_of_hash(RDFSEntry._extract_string(self.jsonDefinition['cims:inverseRoleName']))
        else:
            return None

    def label(self):
        if 'rdfs:label' in self.jsonDefinition:
            return RDFSEntry._extract_text(self.jsonDefinition['rdfs:label']).replace('–', '-').replace('“', '"')\
                        .replace('”', '"').replace('’', "'").replace('°', '').replace('\n', ' ')
        else:
            return None

    def multiplicity(self):
        if 'cims:multiplicity' in self.jsonDefinition:
            return RDFSEntry._get_rid_of_hash(RDFSEntry._extract_string(self.jsonDefinition['cims:multiplicity']))
        else:
            return None

    def range(self):
        if 'rdfs:range' in self.jsonDefinition:
            return RDFSEntry._extract_string(self.jsonDefinition['rdfs:range'])
        else:
            return None

    def stereotype(self):
        if 'cims:stereotype' in self.jsonDefinition:
            return RDFSEntry._extract_string(self.jsonDefinition['cims:stereotype'])
        else:
            return None

    def type(self):
        if 'rdf:type' in self.jsonDefinition:
            return RDFSEntry._extract_string(self.jsonDefinition['rdf:type'])
        else:
            return None

    def version_iri(self):
        if "owl:versionIRI" in self.jsonDefinition:
            return RDFSEntry._extract_string(self.jsonDefinition["owl:versionIRI"])
        else:
            return None

    def subClassOf(self):
        if 'rdfs:subClassOf' in self.jsonDefinition:
            return RDFSEntry._get_rid_of_hash(RDFSEntry._extract_string(self.jsonDefinition['rdfs:subClassOf']))
        else:
            return None

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
                return RDFSEntry._get_about_or_resource(object_dic[0])
        return RDFSEntry._get_about_or_resource(object_dic)

    # The definitions are often contained within a string with a name
    # such as "$rdf:about" or "$rdf:resource", this extracts the
    # useful bit
    def _get_literal(object_dic):
        if '$rdfs:Literal' in object_dic:
            return object_dic['$rdfs:Literal']
        return object_dic


    # The definitions are often contained within a string with a name
    # such as "$rdf:about" or "$rdf:resource", this extracts the
    # useful bit
    def _get_about_or_resource(object_dic):
        if '$rdf:resource' in object_dic:
            return object_dic['$rdf:resource']
        elif '$rdf:about' in object_dic:
            return object_dic['$rdf:about']
        elif '$rdfs:Literal' in object_dic:
            return object_dic['$rdfs:Literal']
        return object_dic

    # Some names are encoded as #name or http://some-url#name
    # This function returns the name
    def _get_rid_of_hash(name):
        tokens = name.split('#')
        if len(tokens) == 1:
            return tokens[0]
        if len(tokens) > 1:
            return tokens[1]
        return name

class CIMComponentDefinition:
    def __init__(self, rdfsEntry):
        self.attribute_list = []
        self.comment = rdfsEntry.comment()
        self.instance_list = []
        self.origin_list = []
        self.super = rdfsEntry.subClassOf()
        self.subclasses = []
        self.stereotype = rdfsEntry.stereotype()

    def attributes(self):
        return self.attribute_list

    def addAttribute(self, attribute):
        self.attribute_list.append(attribute)

    def has_instances(self):
        return len(self.instance_list) > 0

    def instances(self):
        return self.instance_list

    def addInstance(self, instance):
        instance['index'] = len(self.instance_list)
        self.instance_list.append(instance)

    def addAttributes(self, attributes):
        for attribute in attributes:
            self.attribute_list.append(attribute)

    def origins(self):
        return self.origin_list

    def addOrigin(self, origin):
        self.origin_list.append(origin)

    def superClass(self):
        return self.super

    def addSubClass(self, name):
        self.subclasses.append(name)

    def subClasses(self):
        return self.subclasses

    def setSubClasses(self, classes):
        self.subclasses = classes

    def _simple_float_attribute(attr):
        if 'dataType' in attr:
            return attr['label'] == 'value' and attr['dataType'] == '#Float'
        return False

    def is_a_float(self):
        simple_float = False
        for attr in self.attribute_list:
            if CIMComponentDefinition._simple_float_attribute(attr):
                simple_float = True
        for attr in self.attribute_list:
            if not CIMComponentDefinition._simple_float_attribute(attr):
                simple_float = False
        if simple_float:
            return True

        candidate_array = { 'value': False, 'unit': False, 'multiplier': False }
        for attr in self.attribute_list:
            key = attr['label']
            if key in candidate_array:
                candidate_array[key] = True
            else:
                return False
        for key in candidate_array:
            if candidate_array[key] == False:
                return False
        return True

    def is_a_primitive(self):
        return self.stereotype == 'Primitive'

    def is_a_cim_datatype(self):
        return self.stereotype == 'CIMDatatype'

def get_profile_name(descriptions):
    for list_elem in descriptions:
        # only for CGMES-Standard
        rdfsEntry = RDFSEntry(list_elem)
        if rdfsEntry.stereotype() == 'Entsoe':
            return rdfsEntry.about()

def get_short_profile_name(descriptions):
    for list_elem in descriptions:
        # only for CGMES-Standard
        rdfsEntry = RDFSEntry(list_elem)
        if rdfsEntry.label() == 'shortName':
            return rdfsEntry.fixed()


def wrap_and_clean(txt: str, width: int = 120, initial_indent="", subsequent_indent="    ") -> str:
    """
    Used for comments: make them fit within <width> character, including indentation.
    """
    soup = BeautifulSoup(txt, "html.parser")
    return "\n".join(
        textwrap.wrap(
            soup.text,
            width=width,
            initial_indent=initial_indent,
            subsequent_indent=subsequent_indent,
        )
    )


short_package_name = {}
package_listed_by_short_name = {}

profiles = {}

def _rdfs_entry_types(rdfs_entry: RDFSEntry, version)->list:
    """
    Determine the types of RDFS entry. In some case an RDFS entry can be of more than 1 type.
    """
    entry_types = []
    if rdfs_entry.type() != None:
        if rdfs_entry.type() == "http://www.w3.org/2000/01/rdf-schema#Class": # NOSONAR
            entry_types.append("class")
        if rdfs_entry.type() == "http://www.w3.org/1999/02/22-rdf-syntax-ns#Property": # NOSONAR
            entry_types.append("property")
        if rdfs_entry.type() != "http://iec.ch/TC57/1999/rdf-schema-extensions-19990926#ClassCategory": # NOSONAR
            entry_types.append("rest_non_class_category")

    if version == "cgmes_v2_4_15":
        entry_types.extend(_entry_types_version_2(rdfs_entry))
    elif version == "cgmes_v3_0_0":
        entry_types.extend(_entry_types_version_3(rdfs_entry))
    else:
        raise Exception(f"Got version '{version}', but only 'cgmes_v2_4_15' and 'cgmes_v3_0_0' are supported.")

    return entry_types

def _entry_types_version_2(rdfs_entry: RDFSEntry) -> list:
    entry_types=[]
    if rdfs_entry.stereotype() != None:
        if rdfs_entry.stereotype() == "Entsoe" and rdfs_entry.about()[-7:] == "Version":
            entry_types.append("profile_name_v2_4")
        if (
            rdfs_entry.stereotype() == "http://iec.ch/TC57/NonStandard/UML#attribute" # NOSONAR
            and rdfs_entry.label()[0:7] == "baseURI"
        ):
            entry_types.append("profile_iri_v2_4")
        if rdfs_entry.label() == "shortName":
            entry_types.append("short_profile_name_v2_4")
    return entry_types

def _entry_types_version_3(rdfs_entry: RDFSEntry) -> list:
    entry_types=[]
    if rdfs_entry.type() == "http://iec.ch/TC57/1999/rdf-schema-extensions-19990926#ClassCategory": # NOSONAR
        entry_types.append("profile_name_v3")
    if rdfs_entry.about() == "Ontology":
        entry_types.append("profile_iri_v3")
    if rdfs_entry.keyword() is not None:
        entry_types.append("short_profile_name_v3")

    return entry_types


def _add_class(classes_map, rdfs_entry):
    """
    Add class component to classes map
    """
    if rdfs_entry.label() in classes_map:
        logger.error("Class {} already exists".format(rdfs_entry.label()))
    if rdfs_entry.label() != "String":
        classes_map[rdfs_entry.label()] = CIMComponentDefinition(rdfs_entry)


def _add_profile_to_packages(profile_name, short_profile_name, profile_iri):
    """
    Add or append profile_iri
    """
    if profile_name not in profiles and profile_iri:
        profiles[profile_name] = [profile_iri]
    else:
        profiles[profile_name].append(profile_iri)
    if short_profile_name not in package_listed_by_short_name and profile_iri:
        package_listed_by_short_name[short_profile_name] = [profile_iri]
    else:
        package_listed_by_short_name[short_profile_name].append(profile_iri)

def _parse_rdf(input_dic, version):
    classes_map = {}
    profile_name = ""
    profile_iri = None
    attributes = []
    instances = []

    # Generates list with dictionaries as elements
    descriptions = input_dic['rdf:RDF']['rdf:Description']


    # Iterate over list elements
    for list_elem in descriptions:
        rdfsEntry = RDFSEntry(list_elem)
        object_dic = rdfsEntry.asJson()
        rdfs_entry_types = _rdfs_entry_types(rdfsEntry, version)

        if "class" in rdfs_entry_types:
            _add_class(classes_map, rdfsEntry)
        if "property" in rdfs_entry_types:
            attributes.append(object_dic)
        if "rest_non_class_category" in rdfs_entry_types:
            instances.append(object_dic)
        if "profile_name_v2_4" in rdfs_entry_types:
            profile_name = rdfsEntry.about()
        if "profile_name_v3" in rdfs_entry_types:
            profile_name = rdfsEntry.label()
        if "short_profile_name_v2_4" in rdfs_entry_types and rdfsEntry.fixed():
            short_profile_name = rdfsEntry.fixed()
        if "short_profile_name_v3" in rdfs_entry_types:
            short_profile_name = rdfsEntry.keyword()
        if "profile_iri_v2_4" in rdfs_entry_types and rdfsEntry.fixed():
            profile_iri = rdfsEntry.fixed()
        if "profile_iri_v3" in rdfs_entry_types:
            profile_iri = rdfsEntry.version_iri()

    short_package_name[profile_name] = short_profile_name
    package_listed_by_short_name[short_profile_name] = []
    _add_profile_to_packages(profile_name, short_profile_name, profile_iri)
    # Add attributes to corresponding class
    for attribute in attributes:
        clarse = attribute['domain']
        if clarse and classes_map[clarse]:
            classes_map[clarse].addAttribute(attribute)
        else:
            logger.info("Class {} for attribute {} not found.".format(clarse, attribute))

    # Add instances to corresponding class
    for instance in instances:
        clarse = RDFSEntry._get_rid_of_hash(instance['type'])
        if clarse and clarse in classes_map:
            classes_map[clarse].addInstance(instance)
        else:
            logger.info("Class {} for instance {} not found.".format(clarse, instance))

    return {short_profile_name: classes_map}


# This function extracts all information needed for the creation of the python class files like the comments or the
# class name. After the extraction the function write_files is called to write the files with the template engine
# chevron
def _write_python_files(elem_dict, langPack, outputPath, version):

    float_classes = {}
    enum_classes = {}
    primitive_classes = {}
    cim_data_type_classes = {}

    # Iterate over Classes
    for class_definition in elem_dict:
        if elem_dict[class_definition].is_a_float():
            float_classes[class_definition] = True
        if elem_dict[class_definition].has_instances():
            enum_classes[class_definition] = True
        if elem_dict[class_definition].is_a_primitive():
            primitive_classes[class_definition] = True
        if elem_dict[class_definition].is_a_cim_datatype():
            cim_data_type_classes[class_definition] = True

    langPack.set_float_classes(float_classes)
    langPack.set_enum_classes(enum_classes)
    langPack.set_primitive_classes(primitive_classes)
    langPack.set_cim_data_type_classes(cim_data_type_classes)

    for class_name in elem_dict.keys():

        class_details = {
            "attributes": _find_multiple_attributes(elem_dict[class_name].attributes()),
            "class_location": langPack.get_class_location(class_name, elem_dict, outputPath),
            "class_name": class_name,
            "class_origin": elem_dict[class_name].origins(),
            "instances": elem_dict[class_name].instances(),
            "has_instances": elem_dict[class_name].has_instances(),
            "is_a_float": elem_dict[class_name].is_a_float(),
            "is_a_primitive": elem_dict[class_name].is_a_primitive(),
            "is_a_cim_data_type": elem_dict[class_name].is_a_cim_datatype(),
            "langPack": langPack,
            "sub_class_of": elem_dict[class_name].superClass(),
            "sub_classes": elem_dict[class_name].subClasses(),
        }

        # extract comments
        if elem_dict[class_name].comment:
            class_details['class_comment'] = elem_dict[class_name].comment
            class_details['wrapped_class_comment'] = wrap_and_clean(
                elem_dict[class_name].comment, width=116, initial_indent='', subsequent_indent=' ' * 6
            )

        for attribute in class_details['attributes']:
            if "comment" in attribute:
                attribute["comment"] = attribute["comment"].replace('"', "`")
                attribute["comment"] = attribute["comment"].replace("'", "`")
                attribute["wrapped_comment"] = wrap_and_clean(
                    attribute["comment"],
                    width=114 - len(attribute["label"]),
                    initial_indent="",
                    subsequent_indent=" " * 6,
                )
        _write_files(class_details, outputPath, version)

def get_rid_of_hash(name):
    tokens = name.split('#')
    if len(tokens) == 1:
        return tokens[0]
    if len(tokens) > 1:
        return tokens[1]
    return name

def format_class(_range, _dataType):
    if _range == '':
        return get_rid_of_hash(_dataType)
    else:
        return get_rid_of_hash(_range)

def _write_files(class_details, outputPath, version):
    class_details['langPack'].setup(outputPath, package_listed_by_short_name)

    if class_details['sub_class_of'] == None:
        # If class has no subClassOf key it is a subclass of the Base class
        class_details['sub_class_of'] = class_details['langPack'].base['base_class']
        class_details['class_location'] = class_details['langPack'].base['class_location'](version)
        class_details['super_init'] = False
    else:
        # If class is a subclass a super().__init__() is needed
        class_details['super_init'] = True

    # The entry dataType for an attribute is only set for basic data types. If the entry is not set here, the attribute
    # is a reference to another class and therefore the entry dataType is generated and set to the multiplicity
    for i in range(len(class_details['attributes'])):
        if 'dataType' not in class_details['attributes'][i].keys() and 'multiplicity' in class_details['attributes'][i].keys():
            class_details['attributes'][i]['dataType'] = class_details['attributes'][i]['multiplicity']

    for attr in class_details['attributes']:
        _range = ""
        _dataType = ""
        if 'range' in attr:
            _range = attr['range']
        if 'dataType' in attr:
            _dataType = attr['dataType']
        attr['class_name'] = format_class( _range, _dataType )

    class_details['langPack'].run_template( outputPath, class_details )

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
                        # If class already exists in packageDict add attributes to attributes array
                        if len(elem_dict[profile_key][class_key].attributes()) > 0:
                            attributes_array = elem_dict[profile_key][class_key].attributes()
                            profiles_dict[profile_key][class_key].addAttributes(attributes_array)
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
    class_dict = { }

    # Iterate over profiles
    for package_key in profiles_dict.keys():
        # get short name of the profile
        short_name = ""
        if package_key in short_package_name:
            short_name = short_package_name[package_key]
        else:
            short_name = package_key

        # iterate over classes in the current profile
        for class_key in profiles_dict[package_key]:
            # class already defined?
            if class_key not in class_dict:
                # store class and class origin
                class_dict[class_key] = profiles_dict[package_key][class_key]
                class_dict[class_key].addOrigin({'origin': short_name})
                for attr in class_dict[class_key].attributes():
                    # store origin of the attributes
                    attr['attr_origin'] = [{'origin': short_name}]
            else:
                # some inheritance information is stored only in one of the packages. Therefore it has to be checked
                # if the subClassOf attribute is set. See for example TopologicalNode definitions in SV and TP.
                if not class_dict[class_key].superClass():
                    if profiles_dict[package_key][class_key].superClass():
                        class_dict[class_key].super = profiles_dict[package_key][class_key].superClass()

                # check if profile is already stored in class origin list
                multiple_origin = False
                for origin in class_dict[class_key].origins():
                    if short_name == origin['origin']:
                        # origin already stored
                        multiple_origin = True
                        break
                if not multiple_origin:
                    class_dict[class_key].addOrigin({'origin': short_name})

                for attr in profiles_dict[package_key][class_key].attributes():
                    # check if attribute is already in attributes list
                    multiple_attr = False
                    for attr_set in class_dict[class_key].attributes():
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
                        class_dict[class_key].addAttribute(attr)
    return class_dict

def recursively_add_sub_classes(class_dict, class_name):
    newSubClasses = []
    theClass = class_dict[class_name]
    for name in theClass.subClasses():
        newSubClasses.append(name)
        newNewSubClasses = recursively_add_sub_classes(class_dict, name)
        newSubClasses = newSubClasses + newNewSubClasses
    return newSubClasses

def add_sub_classes_of_sub_classes(class_dict):
    for class_name in class_dict:
        class_dict[class_name].setSubClasses(recursively_add_sub_classes(class_dict, class_name))

def add_sub_classes_of_sub_classes_clean(class_dict, source):
    temp = {}
    for class_name in class_dict:
        for name in class_dict[class_name].subClasses():
            if name not in class_dict:
                temp[name] = source[name]
                add_sub_classes_of_sub_classes_clean(temp, source)
    class_dict.update(temp)

# Order classes based on dependency order

def generate_clean_sub_classes(class_dict_with_origins, clean_class_dict):
    for class_name in class_dict_with_origins:
        super_class_name = class_dict_with_origins[class_name].superClass()
        if super_class_name is None and class_dict_with_origins[class_name].has_instances():
            clean_class_dict[class_name] = class_dict_with_origins[class_name]

    for class_name in class_dict_with_origins:
        super_class_name = class_dict_with_origins[class_name].superClass()
        if super_class_name == None and not class_dict_with_origins[class_name].has_instances():
            clean_class_dict[class_name] = class_dict_with_origins[class_name]

    add_sub_classes_of_sub_classes_clean(clean_class_dict, class_dict_with_origins)

def cim_generate(directory, outputPath, version, langPack):
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
    :param outputPath: CGMES version, e.g. version = "cgmes_v2_4_15"
    :param langPack:   python module containing language specific functions
    """
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
            parsed = _parse_rdf(parse_result, version)
            profiles_array.append(parsed)

    # merge multiple profile definitions into one profile
    profiles_dict = _merge_profiles(profiles_array)

    # merge classes from different profiles into one class and track origin of the classes and their attributes
    class_dict_with_origins = _merge_classes(profiles_dict)

    clean_class_dict = {}

    # work out the subclasses for each class by noting the reverse relationship
    for className in class_dict_with_origins:
        superClassName = class_dict_with_origins[className].superClass()
        if superClassName != None:
            if superClassName in class_dict_with_origins:
                superClass = class_dict_with_origins[superClassName]
                superClass.addSubClass(className)
            else:
                print("No match for superClass in dict: :", superClassName)

    # recursively add the subclasses of subclasses
    add_sub_classes_of_sub_classes(class_dict_with_origins)

    generate_clean_sub_classes(class_dict_with_origins, clean_class_dict)

    # get information for writing python files and write python files
    _write_python_files(clean_class_dict, langPack, outputPath, version)

    if "modernpython" in langPack.__name__:
        langPack.resolve_headers(outputPath, version)
    else:
        langPack.resolve_headers(outputPath)

    logger.info("Elapsed Time: {}s\n\n".format(time() - t0))
