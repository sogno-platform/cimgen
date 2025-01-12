import importlib
from dataclasses import Field, fields
from functools import cached_property
from typing import Any, TypeAlias, TypedDict

from pydantic.dataclasses import dataclass

from .config import cgmes_resource_config
from .constants import NAMESPACES
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
        return {self.recommended_profile}

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
                        namespace = self.namespace
                    elif (attr_ns := extra.get("namespace", None)) is None:
                        # The attribute has some extras, but not namespace.
                        # Use the class namespace.
                        namespace = self.namespace
                    else:
                        # The attribute has an explicit namesapce
                        namespace = attr_ns

                    qual_attrs[qualname] = CgmesAttribute(
                        value=getattr(self, shortname),
                        namespace=namespace,
                    )
                    seen_attrs.add(shortname)

        return qual_attrs

    def __str__(self) -> str:
        """Returns the string representation of this resource."""
        return "\n".join([f"{k}={v}" for k, v in sorted(self.to_dict().items())])

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
