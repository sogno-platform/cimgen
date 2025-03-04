package cim4j.utils;

import java.io.BufferedWriter;
import java.io.FileWriter;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Set;

import cim4j.BaseClass;
import cim4j.CimConstants;
import cim4j.IdentifiedObject;
import cim4j.Logging;

/**
 * Convert cim data to rdf.
 */
public class RdfWriter {

	private static final Logging LOG = Logging.getLogger(RdfWriter.class);

	private final Map<String, BaseClass> cimData = new LinkedHashMap<>();

	/**
	 * Add cim data as map of rdfid to cim object.
	 *
	 * @param newCimData cim data as map of rdfid to cim object
	 */
	public void addCimData(Map<String, BaseClass> newCimData) {
		cimData.putAll(newCimData);
	}

	/**
	 * Get cim data.
	 *
	 * @return cim data as map of rdfid to cim object
	 */
	public Map<String, BaseClass> getCimData() {
		return Collections.unmodifiableMap(cimData);
	}

	/**
	 * Clear cim data.
	 */
	public void clearCimData() {
		cimData.clear();
	}

	/**
	 * Convert the cim data to a string containing a rdf document.
	 *
	 * @return cim data as rdf string
	 */
	public String convertCimData() {
		var usedNamespaces = getUsedNamespaces();

		var rdfLines = new StringBuilder();
		rdfLines.append("<?xml version='1.0' encoding='utf-8' ?>\n");
		rdfLines.append("<rdf:RDF");
		var nsList = new ArrayList<>(usedNamespaces.keySet());
		Collections.sort(nsList);
		for (var ns : nsList) {
			var url = usedNamespaces.get(ns);
			rdfLines.append(String.format(" xmlns:%s='%s'", ns, url));
		}
		rdfLines.append(">\n");

		int count = 0;
		for (String rdfid : cimData.keySet()) {
			BaseClass cimObj = cimData.get(rdfid);
			var nsObj = getNamespaceKey(cimObj.getClassNamespaceUrl());
			if (nsObj != null && !cimObj.getClass().equals(IdentifiedObject.class)) {
				String cimType = cimObj.debugString();
				rdfLines.append(String.format("  <%s:%s rdf:ID='%s'>\n", nsObj, cimType, rdfid));
				var attrNames = cimObj.getAttributeNames();
				for (String attrName : attrNames) {
					var namespaceUrl = cimObj.getAttributeNamespaceUrl(attrName);
					var nsAttr = getNamespaceKey(namespaceUrl);
					String attrFullName = cimObj.getAttributeFullName(attrName);
					var attrObj = cimObj.getAttribute(attrName);
					if (attrObj != null) {
						if (attrObj.isPrimitive()) {
							var value = attrObj.getValue();
							if (value != null) {
								rdfLines.append(String.format("    <%s:%s>%s</%s:%s>\n", nsAttr, attrFullName,
										value, nsAttr, attrFullName));
							} else {
								LOG.error(String.format("No value for attribute %s of %s(%s)", attrFullName, cimType,
										rdfid));
							}
						} else {
							String attrRdfId = attrObj.getRdfid();
							if (attrRdfId != null) {
								if (attrRdfId.contains("#")) {
									attrRdfId = namespaceUrl + attrRdfId.split("#")[1];
								} else {
									attrRdfId = "#" + attrRdfId;
								}
								rdfLines.append(String.format("    <%s:%s rdf:resource='%s' />\n",
										nsAttr, attrFullName, attrRdfId));
							} else {
								LOG.error(String.format("No rdfid for attribute %s of %s(%s)", attrFullName, cimType,
										rdfid));
							}
						}
					}
				}
				rdfLines.append(String.format("  </%s:%s>\n", nsObj, cimType));
				++count;
			}
		}
		rdfLines.append("</rdf:RDF>\n");

		LOG.info(String.format("Converted %d of %d CIM objects to RDF", count, cimData.size()));
		return rdfLines.toString();
	}

	/**
	 * Write the cim data to a rdf file.
	 *
	 * @param path path of file to write
	 */
	public void writeCimData(String path) {
		String rdf = convertCimData();
		try (var writer = new BufferedWriter(new FileWriter(path, StandardCharsets.UTF_8))) {
			writer.write(rdf);
		} catch (Exception ex) {
			String txt = "Failed to write rdf file";
			LOG.error(txt, ex);
			throw new RuntimeException(txt, ex);
		}
	}

	private Map<java.lang.String, java.lang.String> getUsedNamespaces() {
		Set<java.lang.String> urls = new HashSet<>();
		urls.add(CimConstants.NAMESPACES_MAP.get("rdf"));
		for (String rdfid : cimData.keySet()) {
			BaseClass cimObj = cimData.get(rdfid);
			urls.add(cimObj.getClassNamespaceUrl());
			var attrNames = cimObj.getAttributeNames();
			for (String attrName : attrNames) {
				var attrObj = cimObj.getAttribute(attrName);
				if (attrObj != null) {
					urls.add(cimObj.getAttributeNamespaceUrl(attrName));
				}
			}
		}
		Map<java.lang.String, java.lang.String> namespaces = new HashMap<>();
		for (var url : urls) {
			var ns = getNamespaceKey(url);
			if (ns != null) {
				namespaces.put(ns, url);
			}
		}
		return namespaces;
	}

	private java.lang.String getNamespaceKey(java.lang.String url) {
		for (var entry : CimConstants.NAMESPACES_MAP.entrySet()) {
			if (entry.getValue().equals(url)) {
				return entry.getKey();
			}
		}
		return null;
	}
}
