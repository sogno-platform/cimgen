from dataclasses import fields
from pathlib import Path

import chevron

from pycgmes.utils.base import Base
from pycgmes.utils.constants import NAMESPACES
from pycgmes.utils.profile import BaseProfile, Profile


class Writer:
    """Class for writing CIM RDF/XML files."""

    def __init__(self, objects: dict[str, Base]):
        """Constructor.

        :param objects:  Mapping of rdfid to CIM object.
        """
        self.objects = objects

    def write(
        self, outputfile: str, model_id: str, class_profile_map: dict[str, BaseProfile]
    ) -> dict[BaseProfile, str]:
        """Write CIM RDF/XML files.

        This function writes CIM objects into one or more RDF/XML files separated by profiles.

        Each CIM object will be written to its corresponding profile file depending on class_profile_map.
        But some objects to more than one file if some attribute profiles are not the same as the class profile.

        :param outputfile:         Stem of the output file, resulting files: <outputfile>_<profile.long_name>.xml.
        :param model_id:           Stem of the model IDs, resulting IDs: <model_id>_<profile.long_name>.
        :param class_profile_map:  Mapping of CIM type to profile.
        :return:                   Mapping of profile to outputfile.
        """
        profile_list: list[BaseProfile] = list(Profile)
        profile_list += {p for p in class_profile_map.values() if p not in profile_list}
        profile_file_map: dict[BaseProfile, str] = {}
        for profile in profile_list:
            profile_name = profile.long_name
            full_file_name = outputfile + "_" + profile.long_name + ".xml"
            output = self.generate(profile, model_id + "_" + profile_name, class_profile_map)
            if output:
                with Path.open(Path(full_file_name), "w") as file:
                    file.write(output)
                profile_file_map[profile] = full_file_name
        return profile_file_map

    def generate(self, profile: BaseProfile, model_id: str, class_profile_map: dict[str, BaseProfile]) -> str:
        """Write CIM objects as RDF/XML data to a string.

        This function writes RDF/XML data corresponding to one profile into a string.

        :param profile:            Only data for this profile should be written.
        :param model_id:           Stem of the model IDs, resulting IDs: <modelID>_<profileName>.
        :param class_profile_map:  Mapping of CIM type to profile.
        :return:                   Mapping of profile to outputfile.
        """
        namespaces = [{"key": k, "url": NAMESPACES[k]} for k in ("rdf", "cim", "md")]
        model_description = {
            "id": model_id,
            "description": [{"attr_name": "modelingAuthoritySet", "value": "www.sogno.energy"}],
        }
        for uri in profile.uris:
            model_description["description"].append({"attr_name": "profile", "value": uri})
        main, about = self.sort_attributes_to_profile(profile, class_profile_map)
        output = ""
        if main or about:
            template_path = (Path(__file__).parent / "export_template.mustache").resolve()
            with template_path.open() as file:
                output = chevron.render(
                    file,
                    {
                        "main": main,
                        "about": about,
                        "namespaces": namespaces,
                        "model": [model_description],
                    },
                )
        return output

    def sort_attributes_to_profile(self, profile: BaseProfile, class_profile_map: dict[str, BaseProfile]):
        """Sort CIM objects and their attributes depending on whether the profile is the main profile of the class.

        This function sorts a list of objects to two lists: main and about.
        An object is sorted to main if the profile is the main profile of the class, otherwise to about.
        To each object the attribute infos are stored in the list.
        But it contains only attributes that belongs to the profile.
        If an attribute has more than one possible profile the main profile of the class is preferred.

        :param profile:            Only data for this profile should be taken.
        :param class_profile_map:  Mapping of CIM type to profile.
        :return:                   main list, about list.
        """
        main = []
        about = []
        for rdfid, obj in self.objects.items():
            typ = obj.apparent_name()
            if typ in class_profile_map and Writer.is_class_matching_profile(obj, profile):
                class_profile = class_profile_map[typ]
                main_entry_of_object = class_profile == profile

                attributes = []
                for attr, attr_infos in Writer.get_attribute_infos(obj).items():
                    value = attr_infos["value"]
                    if value and attr != "mRID" and Writer.get_attribute_profile(obj, attr, class_profile) == profile:
                        if isinstance(value, (list, tuple)):
                            attributes.extend(attr_infos | {"value": v} for v in value)
                        else:
                            attributes.append(attr_infos)

                infos = {"id": rdfid, "type": typ, "attributes": attributes}
                if main_entry_of_object:
                    main.append(infos)
                elif attributes:
                    about.append(infos)
        return main, about

    @staticmethod
    def is_class_matching_profile(obj: Base, profile: BaseProfile) -> bool:
        """Check if this profile is a possible profile for this CIM object.

        This function checks if the CIM type of an object contains data for a profile.
        The profile could be the main profile of the type, or the type contains attributes for this profile.

        :param obj:      CIM object to get the CIM type from.
        :param profile:  Profile to check.
        :return:         True/False
        """
        if profile in obj.possible_profiles:
            return True
        return any(profile in profiles for profiles in obj.possible_attribute_profiles.values())

    @staticmethod
    def get_class_profile(obj: Base) -> BaseProfile:
        """Get the main profile of this CIM object.

        This function searches for the main profile of the CIM type of an object.
        If the type contains attributes for different profiles not all data of the object could be written into one
        file. To write the data to as few as possible files the main profile should be that with most of the
        attributes. But some types contain a lot of rarely used special attributes, i.e. attributes for a special
        profile (e.g. TopologyNode has many attributes for TopologyBoundary, but the main profile should be Topology).
        That's why attributes that only belong to one profile are skipped in the search algorithm.

        :param obj:  CIM object to get the CIM type from.
        :return:     Main profile.
        """
        class_profiles = list(obj.possible_profiles)
        if len(class_profiles) == 1:
            return class_profiles[0]
        profile_attributes_map: dict[BaseProfile, list(str)] = {}
        for attr, profiles in obj.possible_attribute_profiles.items():
            ambiguous_profile = len(profiles) > 1
            for profile in profiles:
                if ambiguous_profile and profile in class_profiles:
                    profile_attributes_map.setdefault(profile, []).append(attr)
        count_profile_list: list(tuple[int, BaseProfile]) = []
        for profile, attributes in profile_attributes_map.items():
            count_profile_list.append((-len(attributes), profile))
        return sorted(count_profile_list)[0][1]

    @staticmethod
    def get_class_profile_map(obj_list: list[Base]) -> dict[str, BaseProfile]:
        """Get the main profiles for a list of CIM objects.

        This function searches for the main profile of each CIM type in the object list
        (see getClassProfile for details).

        The result could be used as parameter for the functions: write and generate.
        But it is also possible to optimize the mapping manually for some CIM types before calling these functions.

        :param obj_list:  List of CIM objects.
        :return:          Mapping of CIM type to profile.
        """
        profile_map: dict[str, BaseProfile] = {}
        for obj in obj_list:
            typ = obj.apparent_name()
            if typ not in profile_map:
                profile_map[typ] = Writer.get_class_profile(obj)
        return profile_map

    @staticmethod
    def get_attribute_profile(obj: Base, attr: str, class_profile: BaseProfile) -> BaseProfile | None:
        """Get the profile for this attribute of the CIM object.

        This function searches for the profile of an attribute for the CIM type of an object.
        If the main profile of the type is a possible profile of the attribute it should be choosen.
        Otherwise, the first profile in the list of possible profiles ordered by profile number.

        :param obj:            CIM object to get the CIM type from.
        :param attr:           Attribute to check
        :param class_profile:  Main profile of the CIM type
        :return:               Attribute profile.
        """
        attr_profiles_map = obj.possible_attribute_profiles
        profiles = attr_profiles_map.get(attr, [])
        if class_profile in profiles:
            return class_profile
        if profiles:
            return sorted(profiles)[0]
        return None

    @staticmethod
    def get_attribute_infos(obj: Base) -> dict[str, dict[str, object]]:
        # the class of this object and the parent classes (excluding class "object").
        class_and_parent_classes = obj.__class__.__mro__[:-1]
        attr_infos_map: dict[str, dict[str, object]] = {}
        for cls in reversed(class_and_parent_classes):
            for field in fields(cls):
                attr = field.name
                if attr not in attr_infos_map:
                    attr_name = cls.apparent_name() + "." + attr
                    extra = getattr(field.default, "json_schema_extra", {})
                    if extra.get("is_used"):
                        infos = {
                            "attr_name": attr_name,
                            "namespace": extra.get("namespace", obj.namespace),
                            "value": getattr(obj, attr),
                            "is_class_attribute": extra.get("is_class_attribute"),
                            "is_enum_attribute": extra.get("is_enum_attribute"),
                            "is_list_attribute": extra.get("is_list_attribute"),
                            "is_primitive_attribute": extra.get("is_primitive_attribute"),
                        }
                        attr_infos_map[attr] = infos
        return attr_infos_map
