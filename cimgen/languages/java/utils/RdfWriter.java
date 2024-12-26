package cim4j.utils;

import java.io.BufferedWriter;
import java.io.FileWriter;
import java.nio.charset.StandardCharsets;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.Map;

import cim4j.BaseClass;
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
		var rdfLines = new StringBuilder();
		rdfLines.append("<?xml version='1.0' encoding='utf-8' ?>\n");
		rdfLines.append("<rdf:RDF xmlns:rdf='http://www.w3.org/1999/02/22-rdf-syntax-ns#'\n");
		rdfLines.append("         xmlns:cim='http://iec.ch/TC57/2012/CIM-schema-cim16#'>\n");

		int count = 0;
		for (String rdfid : cimData.keySet()) {
			BaseClass cimObj = cimData.get(rdfid);
			if (!cimObj.getClass().equals(IdentifiedObject.class)) {
				String cimType = cimObj.debugString();
				rdfLines.append(String.format("  <cim:%s rdf:ID='%s'>\n", cimType, rdfid));
				var attrNames = cimObj.getAttributeNames();
				for (String attrName : attrNames) {
					String attrFullName = cimObj.getAttributeFullName(attrName);
					var attrObj = cimObj.getAttribute(attrName);
					if (attrObj != null) {
						if (attrObj.isPrimitive()) {
							var value = attrObj.getValue();
							if (value != null) {
								rdfLines.append(String.format("    <cim:%s>%s</cim:%s>\n", attrFullName,
										value, attrFullName));
							} else {
								LOG.error(String.format("No value for attribute %s of %s(%s)", attrFullName, cimType,
										rdfid));
							}
						} else {
							String attrRdfId = attrObj.getRdfid();
							if (attrRdfId != null) {
								if (!attrRdfId.contains("#")) {
									attrRdfId = "#" + attrRdfId;
								}
								rdfLines.append(String.format("    <cim:%s rdf:resource='%s' />\n",
										attrFullName, attrRdfId));
							} else {
								LOG.error(String.format("No rdfid for attribute %s of %s(%s)", attrFullName, cimType,
										rdfid));
							}
						}
					}
				}
				rdfLines.append(String.format("  </cim:%s>\n", cimType));
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
}
