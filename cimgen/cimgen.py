import logging
import textwrap
import warnings
from pathlib import Path
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
        if self.namespace():
            json_object["namespace"] = self.namespace()
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

    def namespace(self) -> str:
        if "$rdf:about" in self.json_definition:
            about = RDFSEntry._get_about_or_resource(self.json_definition["$rdf:about"])
            return about[: -len(self.about())]
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
        self.origin_list: list[str] = []
        self.superclass: str = rdfs_entry.subclass_of()
        self.superclass_list: list[str] = []
        self.subclass_list: list[str] = []
        self.stereotype: str = rdfs_entry.stereotype()
        self.namespace: str = rdfs_entry.namespace()
        _add_to_used_namespaces(self.namespace)

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

    def origins(self) -> list[str]:
        return self.origin_list

    def add_origin(self, origin: str) -> None:
        self.origin_list.append(origin)

    def subclass_of(self) -> str:
        return self.superclass

    def set_subclass_of(self, name: str) -> None:
        self.superclass = name

    def superclasses(self) -> list[str]:
        return self.superclass_list

    def set_superclasses(self, classes: list[str]) -> None:
        self.superclass_list = classes

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
all_namespaces: dict[str, str] = {"md": "http://iec.ch/TC57/61970-552/ModelDescription/1#"}  # NOSONAR
used_namespaces: list[str] = []


def _rdfs_entry_types(rdfs_entry: RDFSEntry, version: str) -> list[str]:
    """
    Determine the types of RDFS entry. In some case an RDFS entry can be of more than 1 type.
    """
    entry_types: list[str] = []
    if rdfs_entry.type():
        if rdfs_entry.type() == "http://www.w3.org/2000/01/rdf-schema#Class":  # NOSONAR
            entry_types.append("class")
        elif rdfs_entry.type() == "http://www.w3.org/1999/02/22-rdf-syntax-ns#Property":  # NOSONAR
            entry_types.append("property")
        elif rdfs_entry.type() not in (
            "http://iec.ch/TC57/1999/rdf-schema-extensions-19990926#ClassCategory",  # NOSONAR
            "http://www.w3.org/2002/07/owl#Ontology",  # NOSONAR
        ):
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
    # Exclude DifferenceModel definitions
    if rdfs_entry.namespace() == all_namespaces.get("dm"):
        return
    if rdfs_entry.label() in classes_map:
        logger.error(f"Class {rdfs_entry.label()} already exists.")
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

    _parse_namespaces(input_dic["rdf:RDF"])

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
        if _check_attribute_for_class(classes_map, attribute):
            classes_map[attribute["domain"]].add_attribute(attribute)

    # Add enum instances to corresponding class
    for instance in enum_instances:
        clarse = _get_rid_of_hash(instance["type"])
        if clarse and clarse in classes_map:
            classes_map[clarse].add_enum_instance(instance)
        else:
            logger.error(f"Class '{clarse}' for enum instance {instance} not found.")

    return {short_profile_name: classes_map}


# This function extracts all information needed for the creation of the class files like the comments or the
# class name. After the extraction the function _write_files is called to write the files with the template engine
# chevron
def _write_all_files(
    elem_dict: dict[str, CIMComponentDefinition], lang_pack: ModuleType, output_path: str, version: str
) -> None:

    # Setup called only once: make output directory, create base class, create profile class, etc.
    lang_pack.setup(output_path, version, _get_profile_details(package_listed_by_short_name), _get_used_namespaces())

    recommended_class_profiles = _get_recommended_class_profiles(elem_dict)

    for class_name in elem_dict.keys():

        class_details = {
            "attributes": elem_dict[class_name].attributes(),
            "class_location": lang_pack.get_class_location(class_name, elem_dict, version),
            "class_name": class_name,
            "class_origin": _get_sorted_profile_keys(elem_dict[class_name].origins()),
            "class_namespace": _get_namespace(elem_dict[class_name].namespace),
            "enum_instances": elem_dict[class_name].enum_instances(),
            "is_an_enum_class": elem_dict[class_name].is_an_enum_class(),
            "is_a_primitive_class": elem_dict[class_name].is_a_primitive_class(),
            "is_a_datatype_class": elem_dict[class_name].is_a_datatype_class(),
            "lang_pack": lang_pack,
            "subclass_of": elem_dict[class_name].subclass_of(),
            "superclasses": elem_dict[class_name].superclasses(),
            "subclasses": elem_dict[class_name].subclasses(),
            "recommended_class_profile": recommended_class_profiles[class_name],
        }

        # Exclude ModelDescription and DifferenceModel definitions
        if class_details["class_namespace"] in (all_namespaces.get("md"), all_namespaces.get("dm")):
            continue

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
            attribute["attribute_namespace"] = _get_namespace(attribute["namespace"])
            attribute["is_attribute_with_inverse_list"] = _get_bool_string(
                _is_attribute_with_inverse_list(attribute, elem_dict)
            )
            attribute["attr_origin"] = _get_sorted_profile_keys(attribute["attr_origin"])
            _check_inverse_role(attribute, elem_dict)

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

    class_details["lang_pack"].run_template(output_path, class_details)


def _merge_profiles_and_classes(
    profiles_array: list[dict[str, dict[str, CIMComponentDefinition]]]
) -> dict[str, CIMComponentDefinition]:
    """Merge class infos of all profiles.

    This function merges the classes defined in more than one profile file into one class
    with all attributes defined in any profile.
    The origin of the class definitions and the origin of the attributes of a class are tracked
    and used to generate the possible profile list used for the serialization.

    :param profiles_array: List of profiles containing class infos.
    :return:               Map of class name to class info.
    """
    class_dict: dict[str, CIMComponentDefinition] = {}
    # Iterate through array elements
    for elem_dict in profiles_array:
        # Iterate over profile names
        for origin, new_class_dict in elem_dict.items():
            # Iterate over classes and check for multiple class definitions
            for class_key, new_class_infos in new_class_dict.items():
                if class_key in class_dict:
                    _merge_class_infos(class_dict[class_key], new_class_infos, origin)
                else:
                    # store new class and origin
                    new_class_infos.add_origin(origin)
                    for attr in new_class_infos.attributes():
                        attr["attr_origin"] = [origin]
                    class_dict[class_key] = new_class_infos
    return class_dict


def _merge_class_infos(
    class_infos: CIMComponentDefinition, new_class_infos: CIMComponentDefinition, origin: str
) -> None:
    """Merge infos of a class with class infos from another profile file.

    Some information is missing in one of the profile files (e.g. comment), i.e.
    if the information is missing in class_infos it is taken from new_class_infos.
    The merged results are written to class_infos.

    :param class_infos:     Information about a class.
    :param new_class_infos: Information about a class from another profile file.
    """
    # some inheritance information is stored only in one of the packages. Therefore it has to be checked
    # if the subclass_of attribute is set. See for example TopologicalNode definitions in SV and TP.
    if not class_infos.subclass_of():
        class_infos.set_subclass_of(new_class_infos.subclass_of())
    if not class_infos.comment:
        class_infos.comment = new_class_infos.comment
    if origin not in class_infos.origins():
        class_infos.add_origin(origin)
    _check_merge_class(class_infos, new_class_infos)
    for new_attr in new_class_infos.attributes():
        for attr in class_infos.attributes():
            if attr["label"] == new_attr["label"]:
                # attribute already in attributes list, check if origin is new
                origin_list = attr["attr_origin"]
                if origin not in origin_list:
                    origin_list.append(origin)
                _check_merge_attribute(class_infos.about, attr, new_attr)
                break
        else:
            # new attribute
            new_attr["attr_origin"] = [origin]
            class_infos.add_attribute(new_attr)
    for new_enum in new_class_infos.enum_instances():
        for enum in class_infos.enum_instances():
            if new_enum["label"] == enum["label"]:
                _check_merge_enum(class_infos.about, enum, new_enum)
                break
        else:
            class_infos.add_enum_instance(new_enum)


def _add_superclasses_of_superclasses(class_dict: dict[str, CIMComponentDefinition]) -> None:
    """Set the list of superclasses for each class.

    The algorithm searches superclasses of superclasses recursively. The resulting lists are set as attribute
    superclasses in the class definition. They are sorted upwards according to the hierarchy.

    :param class_dict:  Dictionary with all class definitions.
    """
    for class_name in class_dict:
        superclass_list = []
        superclass = class_dict[class_name].subclass_of()
        while superclass:
            superclass_list.append(superclass)
            superclass = class_dict[superclass].subclass_of()
        class_dict[class_name].set_superclasses(superclass_list)


def _add_subclasses_of_subclasses(class_dict: dict[str, CIMComponentDefinition]) -> None:
    """Set the list of subclasses for each class.

    The algorithm searches subclasses of subclasses using the attribute superclasses of all classes. The superclasses
    lists must therefore have been filled beforehand. The resulting lists are set as attribute subclasses in the class
    definition. They are sorted alphabetically.

    :param class_dict:  Dictionary with all class definitions.
    """
    subclasses_map: dict[str, set[str]] = {}
    for class_name in class_dict:
        for superclass in class_dict[class_name].superclasses():
            subclasses_map.setdefault(superclass, set()).add(class_name)
    for class_name in class_dict:
        class_dict[class_name].set_subclasses(sorted(subclasses_map.get(class_name, set())))


def cim_generate(directory: Path, output_path: str, version: str, lang_pack: ModuleType) -> None:
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
    :param output_path: The output directory
    :param version:     CGMES version, e.g. version = "cgmes_v2_4_15"
    :param lang_pack:   python module containing language specific functions
    """
    profiles_array: list[dict[str, dict[str, CIMComponentDefinition]]] = []

    t0 = time()

    # Iterate over RDF files: first in the main directory, than in subdirectories
    for file in sorted(directory.glob("*.rdf")) + sorted(directory.glob("*/**/*.rdf")):
        logger.info(f"Start of parsing file '{file}'.")

        xmlstring = file.read_text(encoding="utf-8")

        # parse RDF files and create a dictionary from the RDF file
        parse_result = xmltodict.parse(xmlstring, attr_prefix="$", cdata_key="_", dict_constructor=dict)
        parsed = _parse_rdf(parse_result, version)
        profiles_array.append(parsed)

    # merge classes from different profiles into one class and track origin of the classes and their attributes
    class_dict_with_origins = _merge_profiles_and_classes(profiles_array)

    # recursively add the superclasses of superclasses and the subclasses of subclasses
    _add_superclasses_of_superclasses(class_dict_with_origins)
    _add_subclasses_of_subclasses(class_dict_with_origins)

    # get information for writing language specific files and write these files
    _write_all_files(class_dict_with_origins, lang_pack, output_path, version)

    lang_pack.resolve_headers(output_path, version)

    logger.info(f"Elapsed Time: {time() - t0}s")


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
    return sorted(profile_key_list, key=lambda p: "0" if p == "EQ" else p)


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
        class_profiles = elem_dict[class_name].origins()
        if len(class_profiles) == 1:
            recommended_class_profiles[class_name] = class_profiles[0]
            continue

        # Count profiles of all attributes of this class and its superclasses
        profile_count_map = {}
        name = class_name
        while name:
            for attribute in elem_dict[name].attributes():
                profiles = attribute["attr_origin"]
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


def _get_namespace(parsed_namespace: str) -> str:
    if parsed_namespace == "#":
        namespace = all_namespaces["cim"]
    else:
        namespace = parsed_namespace
    return namespace


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


def _is_attribute_with_inverse_list(attribute: dict, elem_dict: dict[str, CIMComponentDefinition]) -> bool:
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


def _parse_namespaces(namespace_dict: dict) -> None:
    """Parse the namespaces of the rdf file and save these in the global dictionary all_namespaces.

    If two rdf files contain the same namespace url with different keys only the first key is saved.
    If two rdf files contain the same namespace key with different urls the second url is saved with key ns0, ns1, etc.

    :param namespace_dict: Dictionary which contains the namespace urls with keys "$xmlns:<ns>".
    """
    global all_namespaces
    for k, v in namespace_dict.items():
        if k.startswith("$xmlns:"):
            ns = k.split(":")[1]
            url = v if v.endswith("#") else v + "#"
            if url not in all_namespaces.values():
                if ns in all_namespaces:
                    used = True
                    idx = 0
                    while used:
                        ns = f"ns{idx}"
                        if ns not in all_namespaces:
                            used = False
                        idx += 1
                all_namespaces[ns] = url


def _add_to_used_namespaces(namespace_url: str) -> None:
    """Add a namespace url to the global list used_namespaces.

    :param namespace_url: URL to add to used_namespaces.
    """
    global used_namespaces
    if namespace_url != "#" and namespace_url not in used_namespaces:
        used_namespaces.append(namespace_url)


def _get_used_namespaces() -> dict[str, str]:
    """Construct a dictionary with the namespaces of the global list used_namespaces using keys from all_namespaces.

    If a namespace url is not found in all_namespaces it will be added to all_namespaces with key ns0, ns1, etc.

    :return: Dictionary of used namespaces.
    """
    global all_namespaces
    for url in used_namespaces:
        if url not in all_namespaces.values():
            used = True
            idx = 0
            while used:
                ns = f"ns{idx}"
                if ns not in all_namespaces:
                    used = False
                idx += 1
            all_namespaces[ns] = url
    namespaces = {}
    for ns, url in all_namespaces.items():
        if ns in ("rdf", "md", "cim") or url in used_namespaces:
            namespaces[ns] = url
    return namespaces


def _check_attribute_for_class(classes_map: dict[str, CIMComponentDefinition], attribute: dict) -> bool:
    """Check if the attribute could be added to the corresponding class.

    :param classes_map: Information about all classes.
    :param attribute:   Dictionary with information about an attribute of a class.
    :return:            Is the attribute okay?
    """
    # Exclude ModelDescription and DifferenceModel definitions
    if attribute["namespace"] in (all_namespaces.get("md"), all_namespaces.get("dm")):
        return False
    about = attribute["about"]
    domain = attribute["domain"]
    label = attribute["label"]
    if domain and classes_map.get(domain):
        if about == domain + "." + label:
            return True
        logger.warning(f"Skip attribute '{about}' of domain '{domain}' because of wrong or missing class.")
        return False
    logger.error(f"Class '{domain}' for attribute '{about}' not found.")
    return False


def _check_inverse_role(attribute: dict, elem_dict: dict[str, CIMComponentDefinition]) -> bool:
    """Check if exactly one side of attribute and inverse role is used.

    :param attribute: Dictionary with information about an attribute of a class.
    :param elem_dict: Information about all classes.
    :return:          Is the attribute and inverse role okay?
    """
    ok = True
    about = attribute["about"]
    if "inverse_role" in attribute:
        inverse_role = attribute["inverse_role"]
        inverse_class, inverse_label = inverse_role.split(".")
        for inverse_attribute in elem_dict[inverse_class].attributes():
            if inverse_attribute["label"] == inverse_label:
                if attribute["is_used"] and inverse_attribute["is_used"]:
                    logger.warning(f"Both sides used for attribute '{about}' with inverse role '{inverse_role}'.")
                    ok = False
                elif not attribute["is_used"] and not inverse_attribute["is_used"]:
                    logger.error(f"No side used for attribute '{about}' with inverse role '{inverse_role}'.")
                    ok = False
                inverse_inverse_role = inverse_attribute.get("inverse_role", "")
                if inverse_inverse_role != about:
                    logger.error(
                        f"Wrong inverse role of inverse role for attribute '{about}': '{inverse_inverse_role}'."
                    )
                    ok = False
    elif not attribute["is_used"]:
        logger.error(f"Attribute '{about}' not used, but has no inverse role.")
        ok = False
    return ok


def _check_merge_class(class_infos: CIMComponentDefinition, new_class_infos: CIMComponentDefinition) -> None:
    """Check if there are differences after merging class infos.

    :param class_infos:     Information about a class.
    :param new_class_infos: Merged information about a class.
    """
    if class_infos.superclass != new_class_infos.superclass and new_class_infos.superclass:
        logger.error(
            "Different superclass for class"
            + f" '{class_infos.about}': '{class_infos.superclass}' != '{new_class_infos.superclass}'."
        )
    if _get_namespace(class_infos.namespace) != _get_namespace(new_class_infos.namespace):
        logger.error(
            "Different namespace for class"
            + f" '{class_infos.about}': '{class_infos.namespace}' != '{new_class_infos.namespace}'."
        )
    if class_infos.comment != new_class_infos.comment and new_class_infos.comment:
        logger.warning(
            "Different comment for class"
            + f" '{class_infos.about}': '{class_infos.comment}' != '{new_class_infos.comment}'."
        )
    if (
        class_infos.is_a_primitive_class() != new_class_infos.is_a_primitive_class()
        or class_infos.is_a_datatype_class() != new_class_infos.is_a_datatype_class()
    ):
        logger.warning(
            "Different stereotype for class"
            + f" '{class_infos.about}': '{class_infos.stereotype}' != '{new_class_infos.stereotype}'."
        )


def _check_merge_attribute(class_name: str, attr: dict, new_attr: dict) -> None:
    """Check if there are differences after merging attribute infos.

    :param class_name: Name of the class.
    :param attr:       Dictionary with information about an attribute.
    :param new_attr:   Merged dictionary with information about an attribute.
    """
    name = attr["label"]
    for k, v in attr.items():
        if k in ("attr_origin", "stereotype"):
            continue
        v_new = new_attr.get(k)
        if v != v_new:
            logger.warning(f"Different {k} for attribute '{name}' of class '{class_name}': '{v}' != '{v_new}'.")


def _check_merge_enum(class_name: str, enum: dict, new_enum: dict) -> None:
    """Check if there are differences after merging enum value infos.

    :param class_name: Name of the class.
    :param enum:       Dictionary with information about an enum value.
    :param new_enum:   Merged dictionary with information about an enum value.
    """
    name = enum["label"]
    for k, v in enum.items():
        if k == "index":
            continue
        v_new = new_enum.get(k)
        if v != v_new:
            logger.warning(f"Different {k} for enum '{name}' of class '{class_name}': '{v}' != '{v_new}'.")
