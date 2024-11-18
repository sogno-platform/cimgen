# Drop in dataclass replacement, allowing easier json dump and validation in the future.
import importlib
from lxml import etree
from dataclasses import Field, fields
from functools import cached_property
from typing import Any, TypeAlias, TypedDict, Optional

from pydantic.dataclasses import dataclass

from .constants import NAMESPACES

from .config import cgmes_resource_config
from .profile import BaseProfile


# Config will be inherited.
@dataclass(config=cgmes_resource_config)
class Base:
    """
    Base Class for resources.
    """

    @cached_property
    def possible_profiles(self) -> set[BaseProfile]:
        """
        A resource can be used by multiple profiles. This is the set of profiles
        where this element can be found.
        """
        raise NotImplementedError("Method not implemented because not relevant in Base.")

    @cached_property
    def recommended_profile(self) -> BaseProfile:
        """
        This is the profile with most of the attributes.
        It should be used to write the data to as few as possible files.
        """
        raise NotImplementedError("Method not implemented because not relevant in Base.")

    @cached_property
    def possible_attribute_profiles(self) -> dict[str, list[BaseProfile]]:
        """
        Mapping of attribute to the list of possible profiles.
        """
        return {f.name: Base.get_extra_prop(f, "in_profiles") for f in fields(self)}

    @staticmethod
    def parse_json_as(attrs: dict[str, Any]) -> "Base":
        """
        Given a json, returns the original object.
        """
        subclass: str = attrs["__class__"]

        # We want all attributes *except* __class__, and I do not want to modify
        # the dict in params with del() or .pop()
        data_attrs = {k: v for k, v in attrs.items() if k != "__class__"}

        mod = importlib.import_module(f".{subclass}", package="pycgmes.resources")
        # Works because the module and the class have the same name.
        return getattr(mod, subclass)(**data_attrs)

    def to_dict(self) -> dict[str, "CgmesAttributeTypes"]:
        """
        Returns the class as dict, with:
        - only public attributes
        - adding __class__ with the classname (for deserialisation)

        """
        attrs = {f.name: getattr(self, f.name) for f in fields(self)}
        attrs["__class__"] = self.apparent_name()
        return attrs

    @cached_property
    def resource_name(self) -> str:
        """Returns the resource type."""
        return self.__class__.__name__

    @cached_property
    def namespace(self) -> str:
        """Returns the namespace. By default, the namespace is the cim namespace for all resources.
        Custom resources can override this.
        """
        return NAMESPACES["cim"]

    @classmethod  # From python 3.11, you cannot wrap @classmethod in @property anymore.
    def apparent_name(cls) -> str:
        """
        If you create your own custom attributes by subclassing a resource,
        but you do not want the name of your new subclass to appear, you can force the apparent name by
        overriding this method.
        """
        return cls.__name__

    def cgmes_attribute_names_in_profile(self, profile: BaseProfile | None) -> set[Field]:
        """
        Returns all fields accross the parent tree which are in the profile in parameter.

        Mostly useful during export to find all the attributes relevant to one profile only.

        mRID will not be present as a resource attribute in the rdf, it will appear in the id of a resource,
        so is skipped. For instance

        <cim:ConnectivityNode rdf:ID="{Here the mRID}">
            <cim:ConnectivityNode.ConnectivityNodeContainer>blah</cim:ConnectivityNode.ConnectivityNodeContainer>
            {here the mRID will not appear}
        </cim:ConnectivityNode>

        If profile is None, returns all.
        """
        return {
            f
            for f in fields(self)
            if profile is None or (profile in Base.get_extra_prop(f, "in_profiles"))
            if f.name != "mRID"
            if Base.get_extra_prop(f, "is_used")
        }

    def cgmes_attributes_in_profile(self, profile: BaseProfile | None) -> dict[str, "CgmesAttribute"]:
        """
        Returns all attribute values as a dict: fully qualified name => CgmesAttribute.
        Fully qualified names is in the form class_name.attribute_name, where class_name is the
        (possibly parent) class where the attribute is defined.

        This is used mostly in export, where the attributes need to be written in the form:
        <cim:IdentifiedObject.name>3022308-EL-M01-145-SC3</cim:IdentifiedObject.name>
        with thus the parent class included in the attribute name.
        """
        # What will be returned, has the qualname as key...
        qual_attrs: dict[str, CgmesAttribute] = {}
        # ... but we check existence with the unqualified (short) name.
        seen_attrs = set()

        # mro contains itself (so parent might be a misnomer) and object, removed with the [:-1].
        for parent in reversed(self.__class__.__mro__[:-1]):
            for f in fields(parent):
                shortname = f.name
                qualname = f"{parent.apparent_name()}.{shortname}"  # type: ignore
                infos = dict()
                if f not in self.cgmes_attribute_names_in_profile(profile) or shortname in seen_attrs:
                    # Wrong profile or already found from a parent.
                    continue
                else:
                    # Namespace finding
                    # "class namespace" means the first namespace defined in the inheritance tree.
                    # This can go up to Base, which will give the default cim NS.
                    if (extra := getattr(f.default, "json_schema_extra", None)) is None:
                        # The attribute does not have extra metadata. It might be a custom atttribute
                        # without it, or a base type (int...).
                        # Use the class namespace.
                        infos["namespace"] = self.namespace
                    elif extra.get("is_used"):
                        if (extra.get("attribute_namespace", None)) is None:
                            # The attribute has some extras, but not namespace.
                            # Use the class namespace.
                            infos["namespace"] = self.namespace

                        else:
                            # The attribute has an explicit namesapce
                            infos["namespace"] = extra.get("attribute_namespace", self.namespace)
                        # adding the extras, used for xml generation
                        extra_info = {
                            "attr_name": qualname,
                            "is_class_attribute": extra.get("is_class_attribute"),
                            "is_enum_attribute": extra.get("is_enum_attribute"),
                            "is_list_attribute": extra.get("is_list_attribute"),
                            "is_primitive_attribute": extra.get("is_primitive_attribute"),
                            "is_datatype_attribute": extra.get("is_datatype_attribute"),
                            "attribute_class": extra.get("attribute_class"),
                        }
                        infos.update(extra_info)

                    infos["value"] = getattr(self, shortname)

                    qual_attrs[qualname] = CgmesAttribute(infos)
                    seen_attrs.add(shortname)

        return qual_attrs

    def to_xml(self, profile_to_export: BaseProfile, id: Optional[str] = None) -> Optional[etree.Element]:
        """Creates an etree element of self with all non-empty attributes of the profile_to_export
        that are not already defined in the recommanded profile
        This can then be used to generate the xml file of the profile_to_export
        Args:
            profile_to_export (Profile): Profile for which we want to obtain the xml tree (eg. Profile.EQ)
            id (Optional[str], optional): "_mRID", optional: some objects don't have mRID attribute. Defaults to None.
        Returns:
            Optional[etree.Element]: etree describing self for the profile_to_export, None if nothing to export
        """
        profile_attributes = self.cgmes_attributes_in_profile(profile_to_export)
        is_recommanded_profile = self.recommended_profile.value == profile_to_export.value

        if not is_recommanded_profile:
            # remove attributes that are also present in "recommended_profile"
            attributes_main = self.cgmes_attributes_in_profile(self.recommended_profile)
            for key in attributes_main.keys():
                if key in profile_attributes:
                    del profile_attributes[key]
        profile_attributes = self._remove_empty_attributes(profile_attributes)

        if "mRID" in self.to_dict():
            obj_id = "_" + self.mRID
        else:
            obj_id = id

        # if no attribute to export or no mRID, return None
        if profile_attributes == {} or obj_id is None:
            root = None
        else:
            nsmap = NAMESPACES
            # Create root element
            root = etree.Element("{" + self.namespace + "}" + self.resource_name, nsmap=nsmap)

            # Add the ID ass attribute to the root
            rdf_namespace = f"""{{{nsmap["rdf"]}}}"""
            if is_recommanded_profile:
                root.set(rdf_namespace + "ID", obj_id)
            else:
                root.set(rdf_namespace + "about", "#" + obj_id)

            for field_name, attribute in profile_attributes.items():
                # add all attributes relevant to the profile as SubElements
                attr_namespace = attribute["namespace"]
                element_name = f"{{{attr_namespace}}}{field_name}"

                if attribute["is_class_attribute"]:
                    # class_attributes are exported as rdf: resource #_mRID_of_target
                    element = etree.SubElement(root, element_name)
                    element.set(rdf_namespace + "resource", "#" + attribute["value"])
                elif attribute["is_enum_attribute"]:
                    element = etree.SubElement(root, element_name)
                    element.set(rdf_namespace + "resource", nsmap["cim"] + attribute["value"])
                else:
                    element = etree.SubElement(root, element_name)
                    element.text = str(attribute["value"])
        return root

    @staticmethod
    def _remove_empty_attributes(attributes: dict) -> dict:
        for key, attribute in list(attributes.items()):
            # Remove empty attributes
            if attribute["value"] is None or attribute["value"] == "":
                del attributes[key]
            else:
                # Make bool lower str for XML
                if (
                    "is_datatype_attribute" in attribute
                    and attribute["attribute_class"]
                    and attribute["attribute_class"].name == "Boolean"
                ):
                    attribute["value"] = str(attribute["value"]).lower()
        return attributes

    def __str__(self) -> str:
        """Returns the string representation of this resource."""
        return "\n".join([f"{k}={v}" for k, v in sorted(self.to_dict().items())])

    def _parse_xml_fragment(self, xml_fragment: str) -> dict:
        """parses an xml fragment into a dict defining the class attributes

        Args:
            xml_fragment (str): xml string defining an instance of the current class

        Returns:
            attribute_dict (dict): a dictionnary of attributes to create/update the class instance
        """
        attribute_dict = {}
        xml_tree = etree.fromstring(xml_fragment)

        # raise an error if the xml does not describe the expected class
        if not xml_tree.tag.endswith(self.resource_name):
            raise (KeyError(f"The fragment does not correspond to the class {self.resource_name}"))

        # parsing the mRID
        for key, value in xml_tree.attrib.items():
            if key.endswith("ID") or key.endswith("about"):
                if value.startswith("#"):
                    value = value[1:]
                if value.startswith("_"):
                    value = value[1:]
                if hasattr(self, "mRID") and value is not None:
                    attribute_dict["mRID"] = value

        # parsing attributes defined in class
        class_attributes = self.cgmes_attributes_in_profile(None)
        for key, class_attribute in class_attributes.items():
            xml_attribute = xml_tree.findall(".//{*}" + key)
            if len(xml_attribute) != 1:
                continue
            xml_attribute = xml_attribute[0]
            attr = key.rsplit(".")[-1]
            attr_value = None

            # class attributes are pointing to another class/instance defined in .attrib
            if class_attribute["is_class_attribute"]:
                if len(xml_attribute.keys()) == 1:
                    attr_value = xml_attribute.values()[0]
                    if attr_value.startswith("#"):
                        attr_value = attr_value[1:]

            # enum attributes are defined in .attrib and has a prefix ending in "#"
            elif class_attribute["is_enum_attribute"]:
                if len(xml_attribute.keys()) == 1:
                    attr_value = xml_attribute.values()[0]
                    if "#" in attr_value:
                        attr_value = attr_value.rsplit("#")[-1]

            elif class_attribute["is_list_attribute"]:
                # other attributes types are defined in .text
                attr_value = xml_attribute
                attr_value = self.key.append(attr_value)
            else:
                attr_value = xml_attribute.text
                # primitive classes are described in "cim_data_type" allowing to retrieve the data type
                if class_attribute["is_primitive_attribute"] or class_attribute["is_datatype_attribute"]:
                    if class_attribute["attribute_class"].type == bool:
                        attr_value = {"true": True, "false": False}.get(attr_value, None)
                    else:
                        attr_value = class_attribute["attribute_class"].type(attr_value)
            if hasattr(self, attr) and attr_value is not None:
                attribute_dict[attr] = attr_value

        return attribute_dict

    @classmethod
    def from_xml(cls, xml_fragment: str):
        """
        Returns an instance of the class from an xml fragment defining the attributes written in the form:
        <cim:IdentifiedObject.name>...</cim:IdentifiedObject.name>
        example: creating an instance by parsing a fragment from the EQ profile
        """
        attribute_dict = cls()._parse_xml_fragment(xml_fragment)

        # Instantiate the class with the dictionary
        return cls(**attribute_dict)

    @staticmethod
    def get_extra_prop(field: Field, prop: str) -> Any:
        # The field is defined as a pydantic field, not a dataclass field,
        # so access to metadata is a tad different. Furthermore, pyright is confused by extra.
        return field.default.json_schema_extra[prop]  # pyright: ignore[reportAttributeAccessIssue]


CgmesAttributeTypes: TypeAlias = str | int | float | Base | list | None


class CgmesAttribute(TypedDict):
    """
    Describes a CGMES attribute: its value and namespace.
    """

    # Actual value
    value: CgmesAttributeTypes
    # Custom attributes might have something different, given as metadata.
    # See readme for more information.
    namespace: str
