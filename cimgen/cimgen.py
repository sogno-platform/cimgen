import logging
import os
import textwrap
import warnings
import re
from time import time

import xmltodict
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)


class RDFSEntry:
    def __init__(self, jsonObject):
        self.jsonDefinition = jsonObject
        return

    def asJson(self, lang_pack):
        jsonObject = {}
        if self.about() is not None:
            jsonObject["about"] = self.about()
        if self.comment() is not None:
            jsonObject["comment"] = self.comment()
        if self.dataType() is not None:
            jsonObject["dataType"] = self.dataType()
        if self.domain() is not None:
            jsonObject["domain"] = self.domain()
        if self.fixed() is not None:
            jsonObject["isFixed"] = self.fixed()
        if self.label() is not None:
            jsonObject["label"] = self.label()
        if self.multiplicity() is not None:
            jsonObject["multiplicity"] = self.multiplicity()
        if self.range() is not None:
            jsonObject["range"] = self.range()
        if self.stereotype() is not None:
            jsonObject["stereotype"] = self.stereotype()
        if self.type() is not None:
            jsonObject["type"] = self.type()
        if self.subClassOf() is not None:
            jsonObject["subClassOf"] = self.subClassOf()
        if self.inverseRole() is not None:
            jsonObject["inverseRole"] = self.inverseRole()
        jsonObject["is_used"] = _get_bool_string(self.is_used())
        return jsonObject

    def about(self):
        if "$rdf:about" in self.jsonDefinition:
            return _get_rid_of_hash(RDFSEntry._get_about_or_resource(self.jsonDefinition["$rdf:about"]))
        else:
            return None

    # Capitalized True/False is valid in python but not in json.
    # Do not use this function in combination with json.load()
    def is_used(self) -> bool:
        if "cims:AssociationUsed" in self.jsonDefinition:
            return "yes" == RDFSEntry._extract_string(self.jsonDefinition["cims:AssociationUsed"]).lower()
        else:
            return True

    def comment(self):
        if "rdfs:comment" in self.jsonDefinition:
            return (
                RDFSEntry._extract_text(self.jsonDefinition["rdfs:comment"])
                .replace("–", "-")
                .replace("“", '"')
                .replace("”", '"')
                .replace("’", "'")
                .replace("°", "[SYMBOL REMOVED]")
                .replace("º", "[SYMBOL REMOVED]")
                .replace("\n", " ")
            )
        else:
            return None

    def dataType(self):
        if "cims:dataType" in self.jsonDefinition:
            return RDFSEntry._extract_string(self.jsonDefinition["cims:dataType"])
        else:
            return None

    def domain(self):
        if "rdfs:domain" in self.jsonDefinition:
            return _get_rid_of_hash(RDFSEntry._extract_string(self.jsonDefinition["rdfs:domain"]))
        else:
            return None

    def fixed(self):
        if "cims:isFixed" in self.jsonDefinition:
            return RDFSEntry._extract_text(self.jsonDefinition["cims:isFixed"])
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
        if "cims:inverseRoleName" in self.jsonDefinition:
            return _get_rid_of_hash(RDFSEntry._extract_string(self.jsonDefinition["cims:inverseRoleName"]))
        else:
            return None

    def label(self):
        if "rdfs:label" in self.jsonDefinition:
            return (
                RDFSEntry._extract_text(self.jsonDefinition["rdfs:label"])
                .replace("–", "-")
                .replace("“", '"')
                .replace("”", '"')
                .replace("’", "'")
                .replace("°", "")
                .replace("\n", " ")
            )
        else:
            return None

    def multiplicity(self):
        if "cims:multiplicity" in self.jsonDefinition:
            return _get_rid_of_hash(RDFSEntry._extract_string(self.jsonDefinition["cims:multiplicity"]))
        else:
            return None

    def range(self):
        if "rdfs:range" in self.jsonDefinition:
            return RDFSEntry._extract_string(self.jsonDefinition["rdfs:range"])
        else:
            return None

    def stereotype(self):
        if "cims:stereotype" in self.jsonDefinition:
            return RDFSEntry._extract_string(self.jsonDefinition["cims:stereotype"])
        else:
            return None

    def type(self):
        if "rdf:type" in self.jsonDefinition:
            return RDFSEntry._extract_string(self.jsonDefinition["rdf:type"])
        else:
            return None

    def version_iri(self):
        if "owl:versionIRI" in self.jsonDefinition:
            return RDFSEntry._extract_string(self.jsonDefinition["owl:versionIRI"])
        else:
            return None

    def subClassOf(self):
        if "rdfs:subClassOf" in self.jsonDefinition:
            return _get_rid_of_hash(RDFSEntry._extract_string(self.jsonDefinition["rdfs:subClassOf"]))
        else:
            return None

    # Extracts the text out of the dictionary after xmltodict, text is labeled by key '_'
    def _extract_text(object_dic):
        if isinstance(object_dic, list):
            return object_dic[0]["_"]
        elif "_" in object_dic.keys():
            return object_dic["_"]
        elif "$rdfs:Literal" in object_dic.keys():
            return object_dic["$rdfs:Literal"]
        else:
            return ""

    # Extract String out of list or dictionary
    def _extract_string(object_dic):
        if isinstance(object_dic, list):
            if len(object_dic) > 0:
                if isinstance(object_dic[0], str):
                    return object_dic[0]
                return RDFSEntry._get_about_or_resource(object_dic[0])
        return RDFSEntry._get_about_or_resource(object_dic)

    # The definitions are often contained within a string with a name
    # such as "$rdf:about" or "$rdf:resource", this extracts the
    # useful bit
    def _get_literal(object_dic):
        if "$rdfs:Literal" in object_dic:
            return object_dic["$rdfs:Literal"]
        return object_dic

    # The definitions are often contained within a string with a name
    # such as "$rdf:about" or "$rdf:resource", this extracts the
    # useful bit
    def _get_about_or_resource(object_dic):
        if "$rdf:resource" in object_dic:
            return object_dic["$rdf:resource"]
        elif "$rdf:about" in object_dic:
            return object_dic["$rdf:about"]
        elif "$rdfs:Literal" in object_dic:
            return object_dic["$rdfs:Literal"]
        return object_dic


class CIMComponentDefinition:
    def __init__(self, rdfsEntry):
        self.about = rdfsEntry.about()
        self.attribute_list = []
        self.comment = rdfsEntry.comment()
        self.enum_instance_list = []
        self.origin_list = []
        self.super = rdfsEntry.subClassOf()
        self.subclasses = []

    def attributes(self):
        return self.attribute_list

    def addAttribute(self, attribute):
        self.attribute_list.append(attribute)

    def is_an_enum_class(self):
        return len(self.enum_instance_list) > 0

    def enum_instances(self):
        return self.enum_instance_list

    def addEnumInstance(self, instance):
        instance["index"] = len(self.enum_instance_list)
        self.enum_instance_list.append(instance)

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
        if "dataType" in attr:
            return attr["label"] == "value" and attr["dataType"] == "#Float"
        return False

    def is_a_float_class(self):
        if self.about == "Float":
            return True
        simple_float = False
        for attr in self.attribute_list:
            if CIMComponentDefinition._simple_float_attribute(attr):
                simple_float = True
        for attr in self.attribute_list:
            if not CIMComponentDefinition._simple_float_attribute(attr):
                simple_float = False
        if simple_float:
            return True

        candidate_array = {"value": False, "unit": False, "multiplier": False}
        optional_attributes = ["denominatorUnit", "denominatorMultiplier"]
        for attr in self.attribute_list:
            key = attr["label"]
            if key in candidate_array:
                candidate_array[key] = True
            elif key not in optional_attributes:
                return False
        for key in candidate_array:
            if not candidate_array[key]:
                return False
        return True


def get_profile_name(descriptions):
    for list_elem in descriptions:
        # only for CGMES-Standard
        rdfsEntry = RDFSEntry(list_elem)
        if rdfsEntry.stereotype() == "Entsoe":
            return rdfsEntry.about()


def get_short_profile_name(descriptions):
    for list_elem in descriptions:
        # only for CGMES-Standard
        rdfsEntry = RDFSEntry(list_elem)
        if rdfsEntry.label() == "shortName":
            return rdfsEntry.fixed()


def wrap_and_clean(txt: str, width: int = 120, initial_indent="", subsequent_indent="    ") -> str:
    """
    Used for comments: make them fit within <width> character, including indentation.
    """

    # Ignore MarkupResemblesLocatorWarning
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")

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
cim_namespace = ""
profiles = {}


def _rdfs_entry_types(rdfs_entry: RDFSEntry, version) -> list:
    """
    Determine the types of RDFS entry. In some case an RDFS entry can be of more than 1 type.
    """
    entry_types = []
    if rdfs_entry.type() is not None:
        if rdfs_entry.type() == "http://www.w3.org/2000/01/rdf-schema#Class":  # NOSONAR
            entry_types.append("class")
        if rdfs_entry.type() == "http://www.w3.org/1999/02/22-rdf-syntax-ns#Property":  # NOSONAR
            entry_types.append("property")
        if rdfs_entry.type() != "http://iec.ch/TC57/1999/rdf-schema-extensions-19990926#ClassCategory":  # NOSONAR
            entry_types.append("rest_non_class_category")

    if version == "cgmes_v2_4_13" or version == "cgmes_v2_4_15":
        entry_types.extend(_entry_types_version_2(rdfs_entry))
    elif version == "cgmes_v3_0_0":
        entry_types.extend(_entry_types_version_3(rdfs_entry))
    else:
        raise Exception(f"Got version '{version}', but only 'cgmes_v2_4_15' and 'cgmes_v3_0_0' are supported.")

    return entry_types


def _entry_types_version_2(rdfs_entry: RDFSEntry) -> list:
    entry_types = []
    if rdfs_entry.stereotype() is not None:
        if rdfs_entry.stereotype() == "Entsoe" and rdfs_entry.about()[-7:] == "Version":
            entry_types.append("profile_name_v2_4")
        if (
            rdfs_entry.stereotype() == "http://iec.ch/TC57/NonStandard/UML#attribute"  # NOSONAR
            and rdfs_entry.label().startswith("entsoeURI")
        ):
            entry_types.append("profile_iri_v2_4")
        if rdfs_entry.label() == "shortName":
            entry_types.append("short_profile_name_v2_4")
    return entry_types


def _entry_types_version_3(rdfs_entry: RDFSEntry) -> list:
    entry_types = []
    if rdfs_entry.type() == "http://iec.ch/TC57/1999/rdf-schema-extensions-19990926#ClassCategory":  # NOSONAR
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


def _add_profile_to_packages(profile_name, short_profile_name, profile_uri_list):
    """
    Add profile_uris
    """
    if profile_name not in profiles and profile_uri_list:
        profiles[profile_name] = profile_uri_list
    else:
        profiles[profile_name].extend(profile_uri_list)
    if short_profile_name not in package_listed_by_short_name and profile_uri_list:
        package_listed_by_short_name[short_profile_name] = profile_uri_list
    else:
        package_listed_by_short_name[short_profile_name].extend(profile_uri_list)


def _parse_rdf(input_dic, version, lang_pack):
    classes_map = {}
    profile_name = ""
    profile_uri_list = []
    attributes = []
    enum_instances = []

    global cim_namespace
    if not cim_namespace:
        cim_namespace = input_dic["rdf:RDF"].get("$xmlns:cim")

    # Generates list with dictionaries as elements
    descriptions = input_dic["rdf:RDF"]["rdf:Description"]

    # Iterate over list elements
    for list_elem in descriptions:
        rdfsEntry = RDFSEntry(list_elem)
        object_dic = rdfsEntry.asJson(lang_pack)
        rdfs_entry_types = _rdfs_entry_types(rdfsEntry, version)

        if "class" in rdfs_entry_types:
            _add_class(classes_map, rdfsEntry)
        if "property" in rdfs_entry_types:
            attributes.append(object_dic)
        if "rest_non_class_category" in rdfs_entry_types:
            enum_instances.append(object_dic)
        if "profile_name_v2_4" in rdfs_entry_types:
            profile_name = rdfsEntry.about()
        if "profile_name_v3" in rdfs_entry_types:
            profile_name = rdfsEntry.label()
        if "short_profile_name_v2_4" in rdfs_entry_types and rdfsEntry.fixed():
            short_profile_name = rdfsEntry.fixed()
        if "short_profile_name_v3" in rdfs_entry_types:
            short_profile_name = rdfsEntry.keyword()
        if "profile_iri_v2_4" in rdfs_entry_types and rdfsEntry.fixed():
            profile_uri_list.append(rdfsEntry.fixed())
        if "profile_iri_v3" in rdfs_entry_types:
            profile_uri_list.append(rdfsEntry.version_iri())

    short_package_name[profile_name] = short_profile_name
    package_listed_by_short_name[short_profile_name] = []
    _add_profile_to_packages(profile_name, short_profile_name, profile_uri_list)
    # Add attributes to corresponding class
    for attribute in attributes:
        clarse = attribute["domain"]
        if clarse and classes_map[clarse]:
            classes_map[clarse].addAttribute(attribute)
        else:
            logger.info("Class {} for attribute {} not found.".format(clarse, attribute))

    # Add enum instances to corresponding class
    for instance in enum_instances:
        clarse = _get_rid_of_hash(instance["type"])
        if clarse and clarse in classes_map:
            classes_map[clarse].addEnumInstance(instance)
        else:
            logger.info("Class {} for enum instance {} not found.".format(clarse, instance))

    return {short_profile_name: classes_map}


# This function extracts all information needed for the creation of the python class files like the comments or the
# class name. After the extraction the function write_files is called to write the files with the template engine
# chevron
def _write_python_files(elem_dict, lang_pack, output_path, version):

    # Setup called only once: make output directory, create base class, create profile class, etc.
    lang_pack.setup(output_path, _get_profile_details(package_listed_by_short_name), cim_namespace)

    float_classes = {}
    enum_classes = {}

    # Iterate over Classes
    for class_definition in elem_dict:
        if elem_dict[class_definition].is_a_float_class():
            float_classes[class_definition] = True
        if elem_dict[class_definition].is_an_enum_class():
            enum_classes[class_definition] = True

    lang_pack.set_float_classes(float_classes)
    lang_pack.set_enum_classes(enum_classes)

    recommended_class_profiles = _get_recommended_class_profiles(elem_dict)

    for class_name in elem_dict.keys():

        class_details = {
            "attributes": _find_multiple_attributes(elem_dict[class_name].attributes()),
            "class_location": lang_pack.get_class_location(class_name, elem_dict, version),
            "class_name": class_name,
            "class_origin": elem_dict[class_name].origins(),
            "enum_instances": elem_dict[class_name].enum_instances(),
            "is_an_enum_class": elem_dict[class_name].is_an_enum_class(),
            "is_a_float_class": elem_dict[class_name].is_a_float_class(),
            "langPack": lang_pack,
            "sub_class_of": elem_dict[class_name].superClass(),
            "sub_classes": elem_dict[class_name].subClasses(),
            "recommended_class_profile": recommended_class_profiles[class_name],
        }

        # extract comments
        if elem_dict[class_name].comment:
            class_details["class_comment"] = elem_dict[class_name].comment
            class_details["wrapped_class_comment"] = wrap_and_clean(
                elem_dict[class_name].comment,
                width=116,
                initial_indent="",
                subsequent_indent=" " * 6,
            )

        for attribute in class_details["attributes"]:
            if "comment" in attribute:
                attribute["comment"] = attribute["comment"].replace('"', "`")
                attribute["comment"] = attribute["comment"].replace("'", "`")
                attribute["wrapped_comment"] = wrap_and_clean(
                    attribute["comment"],
                    width=114 - len(attribute["label"]),
                    initial_indent="",
                    subsequent_indent=" " * 6,
                )
            attribute_class = _get_attribute_class(attribute)
            is_an_enum_class = attribute_class in elem_dict and elem_dict[attribute_class].is_an_enum_class()
            attribute_type = _get_attribute_type(attribute, is_an_enum_class)
            attribute["is_class_attribute"] = _get_bool_string(attribute_type == "class")
            attribute["is_enum_attribute"] = _get_bool_string(attribute_type == "enum")
            attribute["is_list_attribute"] = _get_bool_string(attribute_type == "list")
            attribute["is_primitive_attribute"] = _get_bool_string(attribute_type == "primitive")
            attribute["class_name"] = attribute_class

        class_details["attributes"].sort(key=lambda d: d["label"])
        _write_files(class_details, output_path, version)


# Some names are encoded as #name or http://some-url#name
# This function returns the name
def _get_rid_of_hash(name):
    tokens = name.split("#")
    if len(tokens) == 1:
        return tokens[0]
    if len(tokens) > 1:
        return tokens[1]
    return name


def _write_files(class_details, output_path, version):
    if class_details["sub_class_of"] is None:
        # If class has no subClassOf key it is a subclass of the Base class
        class_details["sub_class_of"] = class_details["langPack"].base["base_class"]
        class_details["class_location"] = class_details["langPack"].base["class_location"](version)
        class_details["super_init"] = False
    else:
        # If class is a subclass a super().__init__() is needed
        class_details["super_init"] = True

    # The entry dataType for an attribute is only set for basic data types. If the entry is not set here, the attribute
    # is a reference to another class and therefore the entry dataType is generated and set to the multiplicity
    for i in range(len(class_details["attributes"])):
        if (
            "dataType" not in class_details["attributes"][i].keys()
            and "multiplicity" in class_details["attributes"][i].keys()
        ):
            class_details["attributes"][i]["dataType"] = class_details["attributes"][i]["multiplicity"]

    class_details["langPack"].run_template(output_path, class_details)


# Find multiple entries for the same attribute
def _find_multiple_attributes(attributes_array):
    merged_attributes = []
    for elem in attributes_array:
        found = False
        for i in range(len(merged_attributes)):
            if elem["label"] == merged_attributes[i]["label"]:
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
    class_dict = {}

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
                class_dict[class_key].addOrigin({"origin": short_name})
                for attr in class_dict[class_key].attributes():
                    # store origin of the attributes
                    attr["attr_origin"] = [{"origin": short_name}]
            else:
                # some inheritance information is stored only in one of the packages. Therefore it has to be checked
                # if the subClassOf attribute is set. See for example TopologicalNode definitions in SV and TP.
                if not class_dict[class_key].superClass():
                    if profiles_dict[package_key][class_key].superClass():
                        class_dict[class_key].super = profiles_dict[package_key][class_key].superClass()

                # check if profile is already stored in class origin list
                multiple_origin = False
                for origin in class_dict[class_key].origins():
                    if short_name == origin["origin"]:
                        # origin already stored
                        multiple_origin = True
                        break
                if not multiple_origin:
                    class_dict[class_key].addOrigin({"origin": short_name})

                for attr in profiles_dict[package_key][class_key].attributes():
                    # check if attribute is already in attributes list
                    multiple_attr = False
                    for attr_set in class_dict[class_key].attributes():
                        if attr["label"] == attr_set["label"]:
                            # attribute already in attributes list, check if origin is new
                            multiple_attr = True
                            for origin in attr_set["attr_origin"]:
                                multiple_attr_origin = False
                                if origin["origin"] == short_name:
                                    multiple_attr_origin = True
                                    break
                            if not multiple_attr_origin:
                                # new origin
                                attr_set["attr_origin"].append({"origin": short_name})
                            break
                    if not multiple_attr:
                        # new attribute
                        attr["attr_origin"] = [{"origin": short_name}]
                        class_dict[class_key].addAttribute(attr)
    return class_dict


def recursivelyAddSubClasses(class_dict, class_name):
    newSubClasses = []
    theClass = class_dict[class_name]
    for name in theClass.subClasses():
        newSubClasses.append(name)
        newNewSubClasses = recursivelyAddSubClasses(class_dict, name)
        newSubClasses = newSubClasses + newNewSubClasses
    return newSubClasses


def addSubClassesOfSubClasses(class_dict):
    for className in class_dict:
        class_dict[className].setSubClasses(recursivelyAddSubClasses(class_dict, className))


def cim_generate(directory, output_path, version, lang_pack):
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

    :param directory: path to RDF files containing cgmes ontology,
                      e.g. directory = "./examples/cgmes_schema/cgmes_v2_4_15_schema"
    :param output_path: CGMES version, e.g. version = "cgmes_v2_4_15"
    :param lang_pack:   python module containing language specific functions
    """
    profiles_array = []

    t0 = time()

    # iterate over files in the directory and check if they are RDF files
    for file in sorted(os.listdir(directory)):
        if file.endswith(".rdf"):
            logger.info('Start of parsing file "%s"', file)

            file_path = os.path.join(directory, file)
            xmlstring = open(file_path, encoding="utf8").read()

            # parse RDF files and create a dictionary from the RDF file
            parse_result = xmltodict.parse(xmlstring, attr_prefix="$", cdata_key="_", dict_constructor=dict)
            parsed = _parse_rdf(parse_result, version, lang_pack)
            profiles_array.append(parsed)

    # merge multiple profile definitions into one profile
    profiles_dict = _merge_profiles(profiles_array)

    # merge classes from different profiles into one class and track origin of the classes and their attributes
    class_dict_with_origins = _merge_classes(profiles_dict)

    # work out the subclasses for each class by noting the reverse relationship
    for className in class_dict_with_origins:
        superClassName = class_dict_with_origins[className].superClass()
        if superClassName is not None:
            if superClassName in class_dict_with_origins:
                superClass = class_dict_with_origins[superClassName]
                superClass.addSubClass(className)
            else:
                print("No match for superClass in dict: :", superClassName)

    # recursively add the subclasses of subclasses
    addSubClassesOfSubClasses(class_dict_with_origins)

    # get information for writing python files and write python files
    _write_python_files(class_dict_with_origins, lang_pack, output_path, version)

    lang_pack.resolve_headers(output_path, version)

    logger.info("Elapsed Time: {}s\n\n".format(time() - t0))


def _get_profile_details(cgmes_profile_uris):
    profile_details = []
    sorted_profile_keys = _get_sorted_profile_keys(cgmes_profile_uris.keys())
    for index, profile in enumerate(sorted_profile_keys):
        profile_info = {
            "index": index,
            "short_name": profile,
            "long_name": _extract_profile_long_name(cgmes_profile_uris[profile]),
            "uris": [{"uri": uri} for uri in cgmes_profile_uris[profile]],
        }
        profile_details.append(profile_info)
    return profile_details


def _extract_profile_long_name(profile_uris):
    # Extract name from uri, e.g. "Topology" from "http://iec.ch/TC57/2013/61970-456/Topology/4"
    # Examples of other possible uris: "http://entsoe.eu/CIM/Topology/4/1", "http://iec.ch/TC57/ns/CIM/Topology-EU/3.0"
    # If more than one uri given, extract common part (e.g. "Equipment" from "EquipmentCore" and "EquipmentOperation")
    long_name = ""
    for uri in profile_uris:
        match = re.search(r"/([^/-]*)(-[^/]*)?(/\d+)?/[\d.]+?$", uri)
        if match:
            name = match.group(1)
            if long_name:
                for idx in range(1, len(long_name)):
                    if idx >= len(name) or long_name[idx] != name[idx]:
                        long_name = long_name[:idx]
                        break
            else:
                long_name = name
    return long_name


def _get_sorted_profile_keys(profile_key_list):
    """Sort profiles alphabetically, but "EQ" to the first place.

    Profiles should be always used in the same order when they are written into the enum class Profile.
    The same order should be used if one of several possible profiles is to be selected.

    :param profile_key_list: List of short profile names.
    :return:                 Sorted list of short profile names.
    """
    return sorted(profile_key_list, key=lambda x: x == "EQ" and "0" or x)


def _get_recommended_class_profiles(elem_dict):
    """Get the recommended profiles for all classes.

    This function searches for the recommended profile of each class.
    If the class contains attributes for different profiles not all data of the object could be written into one file.
    To write the data to as few as possible files the class profile should be that with most of the attributes.
    But some classes contain a lot of rarely used special attributes, i.e. attributes for a special profile
    (e.g. TopologyNode has many attributes for TopologyBoundary, but the class profile should be Topology).
    That's why attributes that only belong to one profile are skipped in the search algorithm.

    :param elem_dict: Information about all classes.
                      Used are here possible class profiles (elem_dict[class_name].origins()),
                      possible attribute profiles (elem_dict[class_name].attributes()[*]["attr_origin"])
                      and the superclass of each class (elem_dict[class_name].superClass()).
    :return:          Mapping of class to profile.
    """
    recommended_class_profiles = {}
    for class_name in elem_dict.keys():
        class_origin = elem_dict[class_name].origins()
        class_profiles = [origin["origin"] for origin in class_origin]
        if len(class_profiles) == 1:
            recommended_class_profiles[class_name] = class_profiles[0]
            continue

        # Count profiles of all attributes of this class and its superclasses
        profile_count_map = {}
        name = class_name
        while name:
            for attribute in _find_multiple_attributes(elem_dict[name].attributes()):
                profiles = [origin["origin"] for origin in attribute["attr_origin"]]
                ambiguous_profile = len(profiles) > 1
                for profile in profiles:
                    if ambiguous_profile and profile in class_profiles:
                        profile_count_map.setdefault(profile, []).append(attribute["label"])
            name = elem_dict[name].superClass()

        # Set the profile with most attributes as recommended profile for this class
        if profile_count_map:
            max_count = max(len(v) for v in profile_count_map.values())
            filtered_profiles = [k for k, v in profile_count_map.items() if len(v) == max_count]
            recommended_class_profiles[class_name] = _get_sorted_profile_keys(filtered_profiles)[0]
        else:
            recommended_class_profiles[class_name] = _get_sorted_profile_keys(class_profiles)[0]
    return recommended_class_profiles


def _get_attribute_class(attribute: dict) -> str:
    """Get the class name of an attribute.

    :param attribute: Dictionary with information about an attribute of a class.
    :return:          Class name of the attribute.
    """
    name = attribute.get("range") or attribute.get("dataType")
    return _get_rid_of_hash(name)


def _get_attribute_type(attribute: dict, is_an_enum_class: bool) -> str:
    """Get the type of an attribute: "class", "enum", "list", or "primitive".

    :param attribute:        Dictionary with information about an attribute of a class.
    :param is_an_enum_class: Is this attribute an enumation?
    :return:                 Type of the attribute.
    """
    so_far_not_primitive = _get_attribute_class(attribute) in (
        "Date",
        "DateTime",
        "MonthDay",
        "Status",
        "StreetAddress",
        "StreetDetail",
        "TownDetail",
    )
    attribute_type = "class"
    if "dataType" in attribute and not so_far_not_primitive:
        attribute_type = "primitive"
    elif is_an_enum_class:
        attribute_type = "enum"
    elif attribute.get("multiplicity") in ("M:0..n", "M:1..n"):
        attribute_type = "list"
    return attribute_type


def _get_bool_string(bool_value: bool) -> str:
    """Convert boolean value into a string which is usable in both Python and Json.

    Valid boolean values in Python are capitalized True/False.
    But these values are not valid in Json.
    Strings with value "true" and "" are recognized as True/False in both languages.

    :param bool_value: Valid boolean value.
    :return:           String "true" for True and "" for False.
    """
    if bool_value:
        return "true"
    else:
        return ""
