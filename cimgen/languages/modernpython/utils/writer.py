from lxml import etree
from pydantic import BaseModel
from .constants import NAMESPACES
from .profile import BaseProfile, Profile
from typing import Dict, Optional


class Writer(BaseModel):
    """Class for writing CIM RDF/XML files

    Args:
        objects (dict): Mapping of rdfid to CIM object
        Model_metadata (Optional[Dict[str, str]]): any additional data to add in header
            default = {"modelingAuthoritySet": "www.sogno.energy" }
    """

    objects: Dict
    writer_metadata: Dict[str, str] = {}

    def write(
        self,
        outputfile: str,
        model_id: str,
        class_profile_map: Dict[str, BaseProfile] = {},
        custom_namespaces: Dict[str, str] = {},
    ) -> dict[BaseProfile, str]:
        """Write CIM RDF/XML files.
        This function writes CIM objects into one or more RDF/XML files separated by profiles.
        Each CIM object will be written to its corresponding profile file depending on class_profile_map.
        But some objects to more than one file if some attribute profiles are not the same as the class profile.

        Args:
            outputfile (str): Stem of the output file, resulting files: <outputfile>_<profile.long_name>.xml.
            model_id (str): Stem of the model IDs, resulting IDs: <model_id>_<profile.long_name>.
            class_profile_map Optional[Dict[str, str]:  Mapping of CIM type to profile.
            custom_namespaces Optional[Dict[str, str]: {"namespace_prefix": "namespace_uri"}

        Returns:
            Mapping of profile to outputfile.
        """
        profile_list: list[BaseProfile] = list(Profile)
        if class_profile_map:
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

    def _generate(
        self, profile: BaseProfile, model_id: str, custom_namespaces: Dict[str, str] = {}
    ) -> Optional[etree.ElementTree]:
        """Write CIM objects as RDF/XML data to a string.

        This function creates RDF/XML tree corresponding to one profile.

        Args:
            profile (BaseProfile):    Only data for this profile should be written.
            model_id (str):   Stem of the model IDs, resulting IDs: <modelID>_<profileName>.
            custom_namespaces Optional[Dict[str, str]]: {"namespace_prefix": "namespace_uri"}

        Returns:
            etree of the profile
        """
        writer_info = {"modelingAuthoritySet": "www.sogno.energy"}
        writer_info.update(self.writer_metadata)
        fullmodel = {
            "id": model_id,
            "Model": writer_info,
        }
        for uri in profile.uris:
            fullmodel["Model"].update({"profile": uri})

        nsmap = NAMESPACES
        nsmap.update(custom_namespaces)

        rdf_namespace = f"""{{{nsmap["rdf"]}}}"""
        md_namespace = f"""{{{nsmap["md"]}}}"""

        root = etree.Element(rdf_namespace + "RDF", nsmap=nsmap)

        # FullModel header
        model = etree.Element(md_namespace + "FullModel", nsmap=nsmap)
        model.set(rdf_namespace + "about", "#" + fullmodel["id"])
        for key, value in fullmodel["Model"].items():
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
