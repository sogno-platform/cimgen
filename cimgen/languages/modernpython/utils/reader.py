import logging
from importlib import import_module
from importlib.util import find_spec
from typing import Literal

from lxml import etree
from pydantic import BaseModel, Field

from .profile import Profile

logger = logging.getLogger(__name__)


class Reader(BaseModel):
    """Parses profiles to create the corresponding python objects

    :param cgmes_version_path:  Path to the cgmes resources folder containing the class definition
    :param custom_namespaces:   {"namespace_prefix": "namespace_uri"}
    :param custom_folder:       "path_to_custom_resources_folder"
    """

    cgmes_version_path: str = "pycgmes.resources"
    custom_namespaces: dict[str, str] | None = None
    custom_folder: str | None = None
    logger_grouped: dict[str, dict[str, int]] = Field(default_factory=lambda: {"errors": {}, "info": {}})
    import_result: dict = Field(default_factory=lambda: {"meta_info": {}, "topology": {}})

    def parse_profiles(self, xml_files: list[str], start_dict: dict | None = None):
        """Parses all profiles contained in xml_files and returns a list containing
        all the objects defined in the profiles "mRID": Object\n
        Errors encounterd in the parsing can be recovered in Reader.logger_grouped

        :param xml_files:   List of the path to all the profiles to parse
        :param start_dict:  To parse profiles on top of an existing list dict(meta_info, topology)

        :return:            ["topology": dict of all the objects defined in the profiles {"mRID": Object}, "meta_info"]
        """
        if start_dict:
            self.import_result = start_dict
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
        """creates/updates the python objects with the information of xml_file

        :param xml_file:        Path to the profile
        :param bases:           Contains the possible namespaces uris defining the classes, can be custom
        :param namespace_rdf:   rdf namespace uri
        """
        context = etree.iterparse(xml_file, ("start", "end"))
        level = 0

        for event, elem in context:
            if event == "end":
                level -= 1
            if event == "start":
                level += 1

            class_namespace = next((namespace for namespace in bases if str(elem.tag).startswith(namespace)), None)
            if event == "start" and class_namespace is not None and level == 2:
                class_name, uuid = self._extract_classname_uuid(elem, class_namespace, namespace_rdf)
                if uuid is not None:
                    self._process_element(class_name, uuid, elem)
            # Check which package is read
            elif event == "end":
                self._check_metadata(elem)

    @staticmethod
    def _extract_classname_uuid(elem, class_namespace: str, namespace_rdf: str) -> tuple:
        """Extracts class name and instance uuid ("mRID")

        :param elem: description of the instance for the given profile
        :param class_namespace: namespace uri defining the class
        :param namespace_rdf: rdf namespace uri

        :return:    class_name, uuid  (example "ACLineSgement", instance_uuid: "mRID")
        """
        class_name = elem.tag[len(class_namespace) :]
        uuid = elem.get("{%s}ID" % namespace_rdf)
        if uuid is None:
            uuid = elem.get("{%s}about" % namespace_rdf)
            if uuid is not None:
                uuid = uuid[1:]
        if uuid.startswith("_"):
            uuid = uuid[1:]
        return class_name, uuid

    def _process_element(self, class_name: str, uuid: str, elem):
        """Creates or updates (if an object with the same uuid exists)
        an instance of the class based on the fragment of the profile

        :param class_name:      Name of the class of the instance to create/update (example: ACLineSegment)
        :param uuid:            mRID
        :param elem:            description of the instance for the given profile
        """
        topology = self.import_result["topology"]
        elem_str = etree.tostring(elem, encoding="utf-8")
        try:
            # Import the module for the CGMES object.
            module_name = self._get_path_to_module(class_name)
            module = import_module(module_name)

            klass = getattr(module, class_name)
            if uuid not in topology:
                topology[uuid] = klass().from_xml(elem_str)
                info_msg = "CIM object {} created".format(module_name.split(".")[-1])
            else:
                obj = topology[uuid]
                obj.update_from_xml(elem_str)
                info_msg = "CIM object {} updated".format(module_name.split(".")[-1])
            self._log_message("info", info_msg)

        except ModuleNotFoundError:
            error_msg = "Module {} not implemented".format(class_name)
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
        elif "author" not in self.import_result["meta_info"].keys():
            if any(author_field in elem.tag for author_field in ("Model.createdBy", "Model.modelingAuthoritySet")):
                self.import_result["meta_info"]["author"] = elem.text

    # Returns a map of class_namespace to namespace for the given XML file.
    @staticmethod
    def _get_namespaces(source) -> dict:
        """Recovers the namespaces defined at the beginning of the xml file without reading the complete file."""
        namespaces = {}
        events = ("end", "start-ns")
        for event, elem in etree.iterparse(source, events):
            if event == "start-ns" and elem is not None:
                # Corresponds to the attributes defined in <rdf:RDF ...>
                class_namespace, ns = elem
                namespaces[class_namespace] = ns
            elif event == "end":
                # Stops once the first attribute that is not a namespace is read (</...>)
                break

        return namespaces

    # Returns the RDF Namespace from the namespaces dictionary
    def _get_rdf_namespace(self) -> str:
        try:
            namespace = self.import_result["meta_info"]["namespaces"]["rdf"]
        except KeyError:
            namespace = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"  # NOSONAR
            logger.warning("No rdf namespace found. Using %s" % namespace)
        return namespace

    def _get_path_to_module(self, class_name: str) -> str:
        if self.custom_folder and find_spec(self.custom_folder + "." + class_name):
            path_to_module = self.custom_folder + "." + class_name
        else:
            path_to_module = self.cgmes_version_path + "." + class_name
        return path_to_module

    def _log_message(self, log_type: Literal["errors", "info"], message: str):
        self.logger_grouped[log_type].setdefault(message, 0)
        self.logger_grouped[log_type][message] += 1
