import logging
import os
import textwrap
import warnings
from time import time
from types import ModuleType

import xmltodict
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)


class RDFSEntry:
    def __init__(self, json_object: dict):
        self.json_definition = json_object
        return

    def as_json(self) -> dict[str, str]:
        json_object = {}
        if self.about():
            json_object["about"] = self.about()
        if self.comment():
            json_object["comment"] = self.comment()
        if self.datatype():
            json_object["datatype"] = self.datatype()
        if self.domain():
            json_object["domain"] = self.domain()
        if self.is_fixed():
            json_object["is_fixed"] = self.is_fixed()
        if self.label():
            json_object["label"] = self.label()
        if self.multiplicity():
            json_object["multiplicity"] = self.multiplicity()
        if self.range():
            json_object["range"] = self.range()
        if self.stereotype():
            json_object["stereotype"] = self.stereotype()
        if self.type():
            json_object["type"] = self.type()
        if self.subclass_of():
            json_object["subclass_of"] = self.subclass_of()
        if self.inverse_role():
            json_object["inverse_role"] = self.inverse_role()
        json_object["is_used"] = _get_bool_string(self.is_used())
        return json_object

    def about(self) -> str:
        if "$rdf:about" in self.json_definition:
            return _get_rid_of_hash(RDFSEntry._get_about_or_resource(self.json_definition["$rdf:about"]))
        else:
            return ""

    # Capitalized True/False is valid in python but not in json.
    # Do not use this function in combination with json.load()
    def is_used(self) -> bool:
        if "cims:AssociationUsed" in self.json_definition:
            return "yes" == RDFSEntry._extract_string(self.json_definition["cims:AssociationUsed"]).lower()
        else:
            return True

    def comment(self) -> str:
        if "rdfs:comment" in self.json_definition:
            return (
                RDFSEntry._extract_text(self.json_definition["rdfs:comment"])
                .replace("–", "-")
                .replace("“", '"')
                .replace("”", '"')
                .replace("’", "'")
                .replace("°", "[SYMBOL REMOVED]")
                .replace("º", "[SYMBOL REMOVED]")
                .replace("\n", " ")
            )
        else:
            return ""

    def datatype(self) -> str:
        if "cims:dataType" in self.json_definition:
            return RDFSEntry._extract_string(self.json_definition["cims:dataType"])
        else:
            return ""

    def domain(self) -> str:
        if "rdfs:domain" in self.json_definition:
            return _get_rid_of_hash(RDFSEntry._extract_string(self.json_definition["rdfs:domain"]))
        else:
            return ""

    def is_fixed(self) -> str:
        if "cims:isFixed" in self.json_definition:
            return RDFSEntry._extract_text(self.json_definition["cims:isFixed"])
        else:
            return ""

    def keyword(self) -> str:
        if "dcat:keyword" in self.json_definition:
            return self.json_definition["dcat:keyword"]
        else:
            return ""

    def inverse_role(self) -> str:
        if "cims:inverseRoleName" in self.json_definition:
            return _get_rid_of_hash(RDFSEntry._extract_string(self.json_definition["cims:inverseRoleName"]))
        else:
            return ""

    def label(self) -> str:
        if "rdfs:label" in self.json_definition:
            return RDFSEntry._extract_text(self.json_definition["rdfs:label"])
        else:
            return ""

    def multiplicity(self) -> str:
        if "cims:multiplicity" in self.json_definition:
            return _get_rid_of_hash(RDFSEntry._extract_string(self.json_definition["cims:multiplicity"]))
        else:
            return ""

    def range(self) -> str:
        if "rdfs:range" in self.json_definition:
            return RDFSEntry._extract_string(self.json_definition["rdfs:range"])
        else:
            return ""

    def stereotype(self) -> str:
        if "cims:stereotype" in self.json_definition:
            return RDFSEntry._extract_string(self.json_definition["cims:stereotype"])
        else:
            return ""

    def type(self) -> str:
        if "rdf:type" in self.json_definition:
            return RDFSEntry._extract_string(self.json_definition["rdf:type"])
        else:
            return ""

    def version_iri(self) -> str:
        if "owl:versionIRI" in self.json_definition:
            return RDFSEntry._extract_string(self.json_definition["owl:versionIRI"])
        else:
            return ""

    def subclass_of(self) -> str:
        if "rdfs:subClassOf" in self.json_definition:
            return _get_rid_of_hash(RDFSEntry._extract_string(self.json_definition["rdfs:subClassOf"]))
        else:
            return ""

    # Extracts the text out of the dictionary after xmltodict, text is labeled by key '_'
    @staticmethod
    def _extract_text(object_dic) -> str:
        if isinstance(object_dic, list):
            return object_dic[0]["_"]
        elif "_" in object_dic.keys():
            return object_dic["_"]
        elif "$rdfs:Literal" in object_dic.keys():
            return object_dic["$rdfs:Literal"]
        return ""

    # Extract String out of list or dictionary
    @staticmethod
    def _extract_string(object_dic) -> str:
        if isinstance(object_dic, list):
            if len(object_dic) > 0:
                if isinstance(object_dic[0], str):
                    return object_dic[0]
                return RDFSEntry._get_about_or_resource(object_dic[0])
        return RDFSEntry._get_about_or_resource(object_dic)

    # The definitions are often contained within a string with a name
    # such as "$rdf:about" or "$rdf:resource", this extracts the
    # useful bit
    @staticmethod
    def _get_about_or_resource(object_dic) -> str:
        if "$rdf:resource" in object_dic:
            return object_dic["$rdf:resource"]
        elif "$rdf:about" in object_dic:
            return object_dic["$rdf:about"]
        elif "$rdfs:Literal" in object_dic:
            return object_dic["$rdfs:Literal"]
        elif type(object_dic) is str:
            return object_dic
        return ""


class CIMComponentDefinition:
    def __init__(self, rdfs_entry: RDFSEntry):
        self.about: str = rdfs_entry.about()
        self.attribute_list: list[dict] = []
        self.comment: str = rdfs_entry.comment()
        self.enum_instance_list: list[dict] = []
        self.origin_list: list[dict] = []
        self.superclass: str = rdfs_entry.subclass_of()
        self.subclass_list: list[str] = []
        self.stereotype: str = rdfs_entry.stereotype()

    def attributes(self) -> list[dict]:
        return self.attribute_list

    def add_attribute(self, attribute: dict) -> None:
        self.attribute_list.append(attribute)

    def is_an_enum_class(self) -> bool:
        return len(self.enum_instance_list) > 0

    def enum_instances(self) -> list[dict]:
        return self.enum_instance_list

    def add_enum_instance(self, instance: dict) -> None:
        instance["index"] = len(self.enum_instance_list)
        self.enum_instance_list.append(instance)

    def origins(self) -> list[dict]:
        return self.origin_list

    def add_origin(self, origin: dict) -> None:
        self.origin_list.append(origin)

    def subclass_of(self) -> str:
        return self.superclass

    def set_subclass_of(self, name: str) -> None:
        self.superclass = name

    def add_subclass(self, name: str) -> None:
        self.subclass_list.append(name)

    def subclasses(self) -> list[str]:
        return self.subclass_list

    def set_subclasses(self, classes: list[str]) -> None:
        self.subclass_list = classes

    def is_a_primitive_class(self) -> bool:
        return self.stereotype == "Primitive"

    def is_a_datatype_class(self) -> bool:
        return self.stereotype == "CIMDatatype"


def _wrap_and_clean(txt: str, width: int = 120, initial_indent="", subsequent_indent="    ") -> str:
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


long_profile_names: dict[str, str] = {}
package_listed_by_short_name: dict[str, list[str]] = {}
cim_namespace: str = ""


def _rdfs_entry_types(rdfs_entry: RDFSEntry, version: str) -> list[str]:
    """
    Determine the types of RDFS entry. In some case an RDFS entry can be of more than 1 type.
    """
    entry_types: list[str] = []
    if rdfs_entry.type():
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


def _entry_types_version_2(rdfs_entry: RDFSEntry) -> list[str]:
    entry_types: list[str] = []
    if rdfs_entry.stereotype():
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


def _entry_types_version_3(rdfs_entry: RDFSEntry) -> list[str]:
    entry_types: list[str] = []
    if rdfs_entry.type() == "http://iec.ch/TC57/1999/rdf-schema-extensions-19990926#ClassCategory":  # NOSONAR
        entry_types.append("profile_name_v3")
    if rdfs_entry.about() == "Ontology":
        entry_types.append("profile_iri_v3")
    if rdfs_entry.keyword():
        entry_types.append("short_profile_name_v3")

    return entry_types


def _add_class(classes_map: dict[str, CIMComponentDefinition], rdfs_entry: RDFSEntry) -> None:
    """
    Add class component to classes map
    """
    if rdfs_entry.label() in classes_map:
        logger.error("Class {} already exists".format(rdfs_entry.label()))
    classes_map[rdfs_entry.label()] = CIMComponentDefinition(rdfs_entry)


def _add_profile_to_packages(profile_name: str, short_profile_name: str, profile_uri_list: list[str]) -> None:
    """
    Add profile_uris and set long profile_name.
    """
    uri_list = package_listed_by_short_name.setdefault(short_profile_name, [])
    for uri in profile_uri_list:
        if uri not in uri_list:
            uri_list.append(uri)
    long_profile_names[short_profile_name] = profile_name.removesuffix("Version").removesuffix("Profile")


def _parse_rdf(input_dic: dict, version: str) -> dict[str, dict[str, CIMComponentDefinition]]:  # NOSONAR
    classes_map: dict[str, CIMComponentDefinition] = {}
    profile_name: str = ""
    short_profile_name: str = ""
    profile_uri_list: list[str] = []
    attributes: list[dict] = []
    enum_instances: list[dict] = []

    global cim_namespace
    if not cim_namespace:
        cim_namespace = input_dic["rdf:RDF"].get("$xmlns:cim")

    # Generates list with dictionaries as elements
    descriptions: list[dict] = input_dic["rdf:RDF"]["rdf:Description"]

    # Iterate over list elements
    for list_elem in descriptions:
        rdfs_entry = RDFSEntry(list_elem)
        object_dic = rdfs_entry.as_json()
        rdfs_entry_types = _rdfs_entry_types(rdfs_entry, version)

        if "class" in rdfs_entry_types:
            _add_class(classes_map, rdfs_entry)
        if "property" in rdfs_entry_types:
            attributes.append(object_dic)
        if "rest_non_class_category" in rdfs_entry_types:
            enum_instances.append(object_dic)
        if not profile_name:
            if "profile_name_v2_4" in rdfs_entry_types:
                profile_name = rdfs_entry.about()
            if "profile_name_v3" in rdfs_entry_types:
                profile_name = rdfs_entry.label()
        if not short_profile_name:
            if "short_profile_name_v2_4" in rdfs_entry_types and rdfs_entry.is_fixed():
                short_profile_name = rdfs_entry.is_fixed()
            if "short_profile_name_v3" in rdfs_entry_types:
                short_profile_name = rdfs_entry.keyword()
        if "profile_iri_v2_4" in rdfs_entry_types and rdfs_entry.is_fixed():
            profile_uri_list.append(rdfs_entry.is_fixed())
        if "profile_iri_v3" in rdfs_entry_types:
            profile_uri_list.append(rdfs_entry.version_iri())

    _add_profile_to_packages(profile_name, short_profile_name, profile_uri_list)

    # Add attributes to corresponding class
    for attribute in attributes:
        clarse = attribute["domain"]
        if clarse and classes_map[clarse]:
            classes_map[clarse].add_attribute(attribute)
        else:
            logger.info("Class {} for attribute {} not found.".format(clarse, attribute))

    # Add enum instances to corresponding class
    for instance in enum_instances:
        clarse = _get_rid_of_hash(instance["type"])
        if clarse and clarse in classes_map:
            classes_map[clarse].add_enum_instance(instance)
        else:
            logger.info("Class {} for enum instance {} not found.".format(clarse, instance))

    return {short_profile_name: classes_map}


# This function extracts all information needed for the creation of the class files like the comments or the
# class name. After the extraction the function _write_files is called to write the files with the template engine
# chevron
def _write_all_files(
    elem_dict: dict[str, CIMComponentDefinition], lang_pack: ModuleType, output_path: str, version: str
) -> None:

    # Setup called only once: make output directory, create base class, create profile class, etc.
    lang_pack.setup(output_path, _get_profile_details(package_listed_by_short_name), cim_namespace)

    recommended_class_profiles = _get_recommended_class_profiles(elem_dict)

    for class_name in elem_dict.keys():

        class_details = {
            "attributes": elem_dict[class_name].attributes(),
            "class_location": lang_pack.get_class_location(class_name, elem_dict, version),
            "class_name": class_name,
            "class_origin": elem_dict[class_name].origins(),
            "enum_instances": elem_dict[class_name].enum_instances(),
            "is_an_enum_class": elem_dict[class_name].is_an_enum_class(),
            "is_a_primitive_class": elem_dict[class_name].is_a_primitive_class(),
            "is_a_datatype_class": elem_dict[class_name].is_a_datatype_class(),
            "lang_pack": lang_pack,
            "subclass_of": elem_dict[class_name].subclass_of(),
            "subclasses": elem_dict[class_name].subclasses(),
            "recommended_class_profile": recommended_class_profiles[class_name],
        }

        # extract comments
        if elem_dict[class_name].comment:
            class_details["class_comment"] = elem_dict[class_name].comment
            class_details["wrapped_class_comment"] = _wrap_and_clean(
                elem_dict[class_name].comment,
                width=116,
                initial_indent="",
                subsequent_indent=" " * 6,
            )

        for attribute in class_details["attributes"]:
            if "comment" in attribute:
                attribute["comment"] = attribute["comment"].replace('"', "`")
                attribute["comment"] = attribute["comment"].replace("'", "`")
                attribute["wrapped_comment"] = _wrap_and_clean(
                    attribute["comment"],
                    width=114 - len(attribute["label"]),
                    initial_indent="",
                    subsequent_indent=" " * 6,
                )
            attribute_class = _get_attribute_class(attribute)
            attribute_type = _get_attribute_type(attribute, elem_dict[attribute_class])
            attribute["is_class_attribute"] = _get_bool_string(attribute_type == "class")
            attribute["is_enum_attribute"] = _get_bool_string(attribute_type == "enum")
            attribute["is_list_attribute"] = _get_bool_string(attribute_type == "list")
            attribute["is_primitive_attribute"] = _get_bool_string(attribute_type == "primitive")
            attribute["is_datatype_attribute"] = _get_bool_string(attribute_type == "datatype")
            attribute["attribute_class"] = attribute_class
            attribute["is_class_attribute_with_inverse_list"] = _get_bool_string(
                _is_class_attribute_with_inverse_list(attribute, elem_dict)
            )

        class_details["attributes"].sort(key=lambda d: d["label"])
        _write_files(class_details, output_path)


# Some names are encoded as #name or http://some-url#name
# This function returns the name
def _get_rid_of_hash(name: str) -> str:
    tokens = name.split("#")
    if len(tokens) == 1:
        return tokens[0]
    if len(tokens) > 1:
        return tokens[1]
    return name


def _write_files(class_details: dict, output_path: str) -> None:
    if not class_details["subclass_of"]:
        # If class has no subclass_of key it is a subclass of the Base class
        class_details["subclass_of"] = class_details["lang_pack"].get_base_class()
        class_details["super_init"] = False
    else:
        # If class is a subclass a super().__init__() is needed
        class_details["super_init"] = True

    # The entry datatype for an attribute is only set for basic data types. If the entry is not set here, the attribute
    # is a reference to another class and therefore the entry datatype is generated and set to the multiplicity
    for i in range(len(class_details["attributes"])):
        if (
            "datatype" not in class_details["attributes"][i].keys()
            and "multiplicity" in class_details["attributes"][i].keys()
        ):
            class_details["attributes"][i]["datatype"] = class_details["attributes"][i]["multiplicity"]

    class_details["lang_pack"].run_template(output_path, class_details)


# If multiple CGMES schema files for one profile are read, e.g. Equipment Core and Equipment Core Short Circuit
# this function merges these into one profile, e.g. Equipment, after this function only one dictionary entry for each
# profile exists. The profiles_array contains one entry for each CGMES schema file which was read.
def _merge_profiles(
    profiles_array: list[dict[str, dict[str, CIMComponentDefinition]]]
) -> dict[str, dict[str, CIMComponentDefinition]]:
    profiles_dict: dict[str, dict[str, CIMComponentDefinition]] = {}
    # Iterate through array elements
    for elem_dict in profiles_array:
        # Iterate over profile names
        for profile_key, new_class_dict in elem_dict.items():
            class_dict = profiles_dict.setdefault(profile_key, {})
            # Iterate over classes and check for multiple class definitions
            for class_key, new_class_infos in new_class_dict.items():
                if class_key in class_dict:
                    class_infos = class_dict[class_key]
                    for new_attr in new_class_infos.attributes():
                        # Iterate over attributes and check for multiple attribute definitions
                        for attr in class_infos.attributes():
                            if new_attr["label"] == attr["label"]:
                                break
                        else:
                            class_infos.add_attribute(new_attr)
                else:
                    class_dict[class_key] = new_class_infos
    return profiles_dict


# This function merges the classes defined in all profiles into one class with all attributes defined in any profile.
# The origin of the class definitions and the origin of the attributes of a class are tracked and used to generate
# the possibleProfileList used for the serialization.
def _merge_classes(profiles_dict: dict[str, dict[str, CIMComponentDefinition]]) -> dict[str, CIMComponentDefinition]:
    class_dict: dict[str, CIMComponentDefinition] = {}
    # Iterate over profiles
    for profile_key, new_class_dict in profiles_dict.items():
        origin = {"origin": profile_key}
        # iterate over classes in the current profile
        for class_key, new_class_infos in new_class_dict.items():
            if class_key in class_dict:
                class_infos = class_dict[class_key]
                # some inheritance information is stored only in one of the packages. Therefore it has to be checked
                # if the subclass_of attribute is set. See for example TopologicalNode definitions in SV and TP.
                if not class_infos.subclass_of():
                    class_infos.set_subclass_of(new_class_infos.subclass_of())
                if origin not in class_infos.origins():
                    class_infos.add_origin(origin)
                for new_attr in new_class_infos.attributes():
                    for attr in class_infos.attributes():
                        if attr["label"] == new_attr["label"]:
                            # attribute already in attributes list, check if origin is new
                            origin_list = attr["attr_origin"]
                            if origin not in origin_list:
                                origin_list.append(origin)
                            break
                    else:
                        # new attribute
                        new_attr["attr_origin"] = [origin]
                        class_infos.add_attribute(new_attr)
            else:
                # store new class and origin
                new_class_infos.add_origin(origin)
                for attr in new_class_infos.attributes():
                    attr["attr_origin"] = [origin]
                class_dict[class_key] = new_class_infos
    return class_dict


def _recursively_add_subclasses(class_dict: dict[str, CIMComponentDefinition], class_name: str) -> list[str]:
    new_subclasses: list[str] = []
    the_class = class_dict[class_name]
    for name in the_class.subclasses():
        new_subclasses.append(name)
        new_new_subclasses = _recursively_add_subclasses(class_dict, name)
        new_subclasses = new_subclasses + new_new_subclasses
    return new_subclasses


def _add_subclasses_of_subclasses(class_dict: dict[str, CIMComponentDefinition]) -> None:
    for class_name in class_dict:
        class_dict[class_name].set_subclasses(_recursively_add_subclasses(class_dict, class_name))


def cim_generate(directory: str, output_path: str, version: str, lang_pack: ModuleType) -> None:
    """Generates cgmes classes from cgmes ontology

    This function uses package xmltodict to parse the RDF files. The _parse_rdf function sorts the classes to
    the corresponding packages. Since multiple files can be read, e.g. Equipment Core and Equipment Short Circuit, the
    classes of these profiles are merged into one profile with _merge_profiles. After that the _merge_classes
    function merges classes defined in multiple profiles into one class and tracks the origin of the class and their
    attributes. This information is stored in the class variable possibleProfileList and used for serialization.
    For more information see the cimexport function in the cimpy package. Finally the _write_all_files function
    extracts all information needed for the creation of the language specific files and creates them
    with the template engine chevron. The attribute version of this function defines the name of the folder where the
    created classes are stored. This folder should not exist and is created in the class generation procedure.

    :param directory: path to RDF files containing cgmes ontology,
                      e.g. directory = "./examples/cgmes_schema/cgmes_v2_4_15_schema"
    :param output_path: CGMES version, e.g. version = "cgmes_v2_4_15"
    :param lang_pack:   python module containing language specific functions
    """
    profiles_array: list[dict[str, dict[str, CIMComponentDefinition]]] = []

    t0 = time()

    # iterate over files in the directory and check if they are RDF files
    for file in sorted(os.listdir(directory)):
        if file.endswith(".rdf"):
            logger.info('Start of parsing file "%s"', file)

            file_path = os.path.join(directory, file)
            xmlstring = open(file_path, encoding="utf-8").read()

            # parse RDF files and create a dictionary from the RDF file
            parse_result = xmltodict.parse(xmlstring, attr_prefix="$", cdata_key="_", dict_constructor=dict)
            parsed = _parse_rdf(parse_result, version)
            profiles_array.append(parsed)

    # merge multiple profile definitions into one profile
    profiles_dict = _merge_profiles(profiles_array)

    # merge classes from different profiles into one class and track origin of the classes and their attributes
    class_dict_with_origins = _merge_classes(profiles_dict)

    # work out the subclasses for each class by noting the reverse relationship
    for class_name in class_dict_with_origins:
        superclass_name = class_dict_with_origins[class_name].subclass_of()
        if superclass_name:
            if superclass_name in class_dict_with_origins:
                superclass = class_dict_with_origins[superclass_name]
                superclass.add_subclass(class_name)
            else:
                logger.error("No match for superclass in dict: %s", superclass_name)

    # recursively add the subclasses of subclasses
    _add_subclasses_of_subclasses(class_dict_with_origins)

    # get information for writing language specific files and write these files
    _write_all_files(class_dict_with_origins, lang_pack, output_path, version)

    lang_pack.resolve_headers(output_path, version)

    logger.info("Elapsed Time: {}s\n\n".format(time() - t0))


def _get_profile_details(cgmes_profile_uris: dict[str, list[str]]) -> list[dict]:
    profile_details: list[dict] = []
    sorted_profile_keys = _get_sorted_profile_keys(list(cgmes_profile_uris.keys()))
    for index, profile in enumerate(sorted_profile_keys):
        profile_info = {
            "index": index,
            "short_name": profile,
            "long_name": long_profile_names[profile],
            "uris": [{"uri": uri} for uri in cgmes_profile_uris[profile]],
        }
        profile_details.append(profile_info)
    return profile_details


def _get_sorted_profile_keys(profile_key_list: list[str]) -> list[str]:
    """Sort profiles alphabetically, but "EQ" to the first place.

    Profiles should be always used in the same order when they are written into the enum class Profile.
    The same order should be used if one of several possible profiles is to be selected.

    :param profile_key_list: List of short profile names.
    :return:                 Sorted list of short profile names.
    """
    return sorted(profile_key_list, key=lambda x: x == "EQ" and "0" or x)


def _get_recommended_class_profiles(elem_dict: dict[str, CIMComponentDefinition]) -> dict[str, str]:
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
                      and the superclass of each class (elem_dict[class_name].subclass_of()).
    :return:          Mapping of class to profile.
    """
    recommended_class_profiles: dict[str, str] = {}
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
            for attribute in elem_dict[name].attributes():
                profiles = [origin["origin"] for origin in attribute["attr_origin"]]
                ambiguous_profile = len(profiles) > 1
                for profile in profiles:
                    # Use condition attribute["is_used"]? For CGMES 2.4.13/2.4.15/3.0.0 the results wouldn't change!
                    if ambiguous_profile and profile in class_profiles:
                        profile_count_map.setdefault(profile, []).append(attribute["label"])
            name = elem_dict[name].subclass_of()

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
    name = attribute.get("range") or attribute.get("datatype") or ""
    return _get_rid_of_hash(name)


def _get_attribute_type(attribute: dict, class_infos: CIMComponentDefinition) -> str:
    """Get the type of an attribute: "class", "datatype", "enum", "list", or "primitive".

    :param attribute:        Dictionary with information about an attribute of a class.
    :param class_infos:      Information about the attribute class.
    :return:                 Type of the attribute.
    """
    attribute_type = "class"
    if class_infos.is_a_datatype_class():
        attribute_type = "datatype"
    elif class_infos.is_a_primitive_class():
        attribute_type = "primitive"
    elif class_infos.is_an_enum_class():
        attribute_type = "enum"
    elif attribute.get("multiplicity") in ("M:0..n", "M:0..2", "M:1..n", "M:2..n"):
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


def _is_class_attribute_with_inverse_list(attribute: dict, elem_dict: dict[str, CIMComponentDefinition]) -> bool:
    """Check if the inverse role of the attribute is a list.

    :param attribute: Dictionary with information about an attribute of a class.
    :param elem_dict: Information about all classes.
    :return:          Is the inverse role of the attribute a list?
    """
    if "inverse_role" in attribute:
        inverse_class, inverse_label = attribute["inverse_role"].split(".")
        for inverse_attribute in elem_dict[inverse_class].attributes():
            if inverse_attribute["label"] == inverse_label:
                attribute_class = _get_attribute_class(inverse_attribute)
                attribute_type = _get_attribute_type(inverse_attribute, elem_dict[attribute_class])
                return attribute_type == "list"
    return False
