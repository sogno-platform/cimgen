from lxml import etree
from .base import Base
from .constants import NAMESPACES
from .profile import BaseProfile, Profile
from typing import Optional


class Writer:
    """Class for writing CIM RDF/XML files."""

    def __init__(self, objects: dict[str, Base]):
        """Constructor.

        :param objects:  Mapping of rdfid to CIM object.
        """
        self.objects = objects

    def write(
        self, outputfile: str, model_id: str, class_profile_map: dict[str, BaseProfile], custom_namespaces: dict
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
            output = self._generate(profile, model_id + "_" + profile_name, custom_namespaces)
            if output:
                output.write(full_file_name, pretty_print=True, xml_declaration=True, encoding="UTF-8")
                profile_file_map[profile] = full_file_name
        return profile_file_map

    def _generate(self, profile: BaseProfile, model_id: str, custom_namespaces) -> Optional[etree.ElementTree]:
        """Write CIM objects as RDF/XML data to a string.

        This function creates RDF/XML tree corresponding to one profile.

        :param profile:            Only data for this profile should be written.
        :param model_id:           Stem of the model IDs, resulting IDs: <modelID>_<profileName>.
        :return:                   etree of the profile
        """
        FullModel = {
            "id": model_id,
            "Model": {"modelingAuthoritySet": "www.sogno.energy"},
        }
        for uri in profile.uris:
            FullModel["Model"].update({"profile": uri})

        nsmap = NAMESPACES
        nsmap.update(custom_namespaces)

        rdf_namespace = f"""{{{nsmap["rdf"]}}}"""
        md_namespace = f"""{{{nsmap["md"]}}}"""

        root = etree.Element(rdf_namespace + "RDF", nsmap=nsmap)

        # FullModel header
        model = etree.Element(md_namespace + "FullModel", nsmap=nsmap)
        model.set(rdf_namespace + "about", "#" + FullModel["id"])
        for key, value in FullModel["Model"].items():
            element = etree.SubElement(model, md_namespace + "Model." + key)
            element.text = value
        root.append(model)

        count = 0
        for id, obj in self.objects.items():
            obj_etree = obj.to_xml(profile_to_export=profile, id=id)
            if obj_etree is not None:
                root.append(obj_etree)
                count += 1
        if count > 0:
            output = etree.ElementTree(root)
        else:
            output = None
        return output
