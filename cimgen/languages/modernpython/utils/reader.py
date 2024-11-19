from lxml import etree
import importlib
import logging
from .profile import Profile
from pydantic import BaseModel, Field
from typing import Dict, Optional, Literal


logger = logging.getLogger(__name__)


class Reader(BaseModel):
    cgmes_version_path: str
    custom_namespaces: Optional[Dict[str, str]] = None
    custom_folder: Optional[Dict[str, str]] = None
    start_dict: Optional[Dict] = None
    logger_grouped: Dict[str, Dict[str, int]] = Field(default_factory=lambda: {"errors": {}, "info": {}})
    import_result: Dict = Field(default_factory=lambda: {"meta_info": {}, "topology": {}})

    def cim_import(self, xml_files):

        self.import_result["meta_info"] = dict(namespaces=self._get_namespaces(xml_files[0]), urls={})
        namespace_rdf = self._get_rdf_namespace()

        bases = ["{" + self.import_result["meta_info"]["namespaces"]["cim"] + "}"]
        if self.custom_namespaces:
            for custom_namespace in self.custom_namespaces.values():
                bases.append("{" + custom_namespace + "}")
        bases = tuple(bases)

        for xml_file in xml_files:
            self._instantiate_classes(xml_file=xml_file, bases=bases, namespace_rdf=namespace_rdf)
        return self.import_result

    def _instantiate_classes(self, xml_file: str, bases: tuple, namespace_rdf: str):

        context = etree.iterparse(xml_file, ("start", "end"))
        _, root = next(context)
        level = 0

        for event, elem in context:
            if event == "end":
                level -= 1
            if event == "start":
                level += 1

            prefix = next((namespace for namespace in bases if elem.tag.startswith(namespace)), None)
            if event == "start" and prefix is not None and level == 1:
                tag, uuid = self._extract_tag_uuid(elem, prefix, namespace_rdf)
                if uuid is not None:
                    self._process_element(tag, uuid, prefix, elem)
            # Check which package is read
            elif event == "end":
                self._check_metadata(elem)

    def _process_element(self, tag, uuid, prefix, elem):
        topology = self.import_result["topology"]
        elem_str = etree.tostring(elem, encoding="utf8")
        try:
            # Import the module for the CGMES object.
            module_name = self._get_path_to_module(prefix) + "." + tag
            module = importlib.import_module(module_name)

            klass = getattr(module, tag)
            if uuid in topology:
                obj = topology[uuid]
                obj.update_from_xml(elem_str)
                info_msg = "CIM object {} updated".format(module_name.split(".")[-1])
            else:
                topology[uuid] = klass().from_xml(elem_str)
                info_msg = "CIM object {} created".format(module_name.split(".")[-1])
            self._log_message("info", info_msg)
        except ModuleNotFoundError:
            error_msg = "Module {} not implemented".format(tag)
            self._log_message("errors", error_msg)
        except Exception as e:
            error_msg = "Could not create/update {}, {}".format(uuid, e)
            self._log_message("errors", error_msg)

    def _check_metadata(self, elem):
        if "Model.profile" in elem.tag:
            for package_key in [e.value for e in Profile]:
                if package_key in elem.text:
                    break
        # the author of all imported files should be the same, avoid multiple entries
        elif "author" in self.import_result["meta_info"].keys():
            pass
        # extract author
        elif "Model.createdBy" in elem.tag:
            self.import_result["meta_info"]["author"] = elem.text
        elif "Model.modelingAuthoritySet" in elem.tag:
            self.import_result["meta_info"]["author"] = elem.text

    # Returns a map of prefix to namespace for the given XML file.
    @staticmethod
    def _get_namespaces(source) -> str:
        namespaces = {}
        events = ("end", "start-ns", "end-ns")
        for event, elem in etree.iterparse(source, events):
            if event == "start-ns":
                prefix, ns = elem
                namespaces[prefix] = ns
            elif event == "end":
                break

        # Reset stream
        if hasattr(source, "seek"):
            source.seek(0)

        return namespaces

    def _extract_tag_uuid(self, elem, prefix: str, namespace_rdf: str) -> tuple:
        tag = elem.tag[len(prefix) :]
        uuid = elem.get("{%s}ID" % namespace_rdf)
        if uuid is None:
            uuid = elem.get("{%s}about" % namespace_rdf)
            if uuid is not None:
                uuid = uuid[1:]
        if uuid is not None:
            if not uuid.startswith("_"):
                uuid = "_" + uuid
        return tag, uuid

    # Returns the RDF Namespace from the namespaces dictionary
    def _get_rdf_namespace(self) -> str:
        try:
            namespace = self.import_result["meta_info"]["namespaces"]["rdf"]
        except KeyError:
            namespace = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
            logger.warning("No rdf namespace found. Using %s" % namespace)
        return namespace

    def _get_path_to_module(self, prefix: str) -> str:
        namespace = prefix[1:-1]
        if self.custom_folder and namespace in self.custom_folder:
            path_to_module = self.custom_folder[namespace]
        else:
            path_to_module = self.cgmes_version_path
        return path_to_module

    def _log_message(self, log_type: Literal["errors", "info"], message: str):
        self.logger_grouped[log_type].setdefault(message, 0)
        self.logger_grouped[log_type][message] += 1
