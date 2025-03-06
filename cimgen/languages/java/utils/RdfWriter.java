package cim4j.utils;

import java.io.BufferedWriter;
import java.io.FileWriter;
import java.io.Writer;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Set;

import javax.xml.stream.XMLOutputFactory;

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
     * Write the CIM data to a RDF file.
     *
     * @param path path of file to write
     */
    public void write(String path) {
        try (var writer = new BufferedWriter(new FileWriter(path, StandardCharsets.UTF_8))) {
            write(writer);
        } catch (Exception ex) {
            String txt = "Failed to write rdf file";
            LOG.error(txt, ex);
            throw new RuntimeException(txt, ex);
        }
    }

    /**
     * Write the CIM data to a stream.
     *
     * @return cim data as rdf string
     */
    public void write(Writer streamWriter) {
        final String RDF = CimConstants.NAMESPACES_MAP.get("rdf");

        try {
            var factory = XMLOutputFactory.newInstance();
            var writer = factory.createXMLStreamWriter(streamWriter);

            writer.writeStartDocument("utf-8", "1.0");
            writer.writeCharacters("\n");

            var usedNamespaces = getUsedNamespaces();
            var nsList = new ArrayList<>(usedNamespaces.keySet());
            Collections.sort(nsList);

            for (var ns : nsList) {
                writer.setPrefix(ns, usedNamespaces.get(ns));
            }

            writer.writeStartElement(RDF, "RDF");

            for (var ns : nsList) {
                writer.writeNamespace(ns, usedNamespaces.get(ns));
            }

            int count = 0;
            for (String rdfid : cimData.keySet()) {
                BaseClass cimObj = cimData.get(rdfid);
                if (!cimObj.getClass().equals(IdentifiedObject.class)) {
                    String cimType = cimObj.debugString();

                    writer.writeCharacters("\n  ");
                    writer.writeStartElement(cimObj.getClassNamespaceUrl(), cimType);
                    writer.writeAttribute(RDF, "ID", rdfid);

                    var attrNames = cimObj.getAttributeNames();
                    for (String attrName : attrNames) {
                        var namespaceUrl = cimObj.getAttributeNamespaceUrl(attrName);
                        String attrFullName = cimObj.getAttributeFullName(attrName);
                        var attrObj = cimObj.getAttribute(attrName);
                        if (attrObj != null) {
                            if (attrObj.isPrimitive()) {
                                var value = attrObj.getValue();
                                if (value != null) {
                                    writer.writeCharacters("\n    ");
                                    writer.writeStartElement(namespaceUrl, attrFullName);
                                    writer.writeCharacters(value.toString());
                                    writer.writeEndElement();
                                } else {
                                    LOG.error(String.format("No value for attribute %s of %s(%s)", attrFullName,
                                            cimType, rdfid));
                                }
                            } else {
                                String attrRdfId = attrObj.getRdfid();
                                if (attrRdfId != null) {
                                    if (!attrRdfId.contains("#")) {
                                        attrRdfId = "#" + attrRdfId;
                                    } else if (attrRdfId.indexOf("#") != 0) {
                                        String[] parts = attrRdfId.split("#");
                                        attrRdfId = namespaceUrl + parts[1];
                                    }
                                    writer.writeCharacters("\n    ");
                                    writer.writeEmptyElement(namespaceUrl, attrFullName);
                                    writer.writeAttribute(RDF, "resource", attrRdfId);
                                } else {
                                    LOG.error(
                                            String.format("No rdfid for attribute %s of %s(%s)", attrFullName, cimType,
                                                    rdfid));
                                }
                            }
                        }
                    }
                    writer.writeCharacters("\n  ");
                    writer.writeEndElement();
                    ++count;
                }
            }
            writer.writeCharacters("\n");
            writer.writeEndDocument();
            writer.writeCharacters("\n");
            writer.close();

            LOG.info(String.format("Written %d of %d CIM objects to RDF", count, cimData.size()));
        } catch (Exception ex) {
            throw new RuntimeException("Error while writing RDF/XML data", ex);
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
