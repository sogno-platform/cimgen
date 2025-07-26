package cim4j.utils;

import java.io.ByteArrayInputStream;
import java.io.FileInputStream;
import java.nio.charset.StandardCharsets;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;

import cim4j.BaseClass;
import cim4j.CimClassMap;
import cim4j.Logging;

/**
 * Read RDF files into a map of rdfid to CIM object.
 */
public class RdfReader {

    private static final Logging LOG = Logging.getLogger(RdfReader.class);

    private final Map<String, BaseClass> model = new LinkedHashMap<>();

    /**
     * Read the CIM data from a list of RDF files.
     *
     * @param pathList List of files to read
     * @return CIM data as map of rdfid to CIM object
     */
    public Map<String, BaseClass> read(List<String> pathList) {
        model.clear();
        for (String path : pathList) {
            int count = model.size();
            long memory = getUsedMemory();
            try (var stream = new FileInputStream(path)) {
                RdfParser.parse(stream, this::createCimObject);
            } catch (Exception ex) {
                String txt = "Error while reading rdf file: " + path;
                LOG.error(txt, ex);
                throw new RuntimeException(txt, ex);
            }
            memory = getUsedMemory() - memory;
            LOG.info(String.format("Read %d CIM objects from %s using %d MByte (%d)", model.size() - count,
                    path, memory / (1024 * 1024), memory));
        }
        setAttributeLinks();
        return model;
    }

    /**
     * Read the CIM data from a list of strings with XML content.
     *
     * @param xmlList Input strings to read
     * @return CIM data as map of rdfid to CIM object
     */
    public Map<String, BaseClass> readFromStrings(List<String> xmlList) {
        model.clear();
        for (String xml : xmlList) {
            int count = model.size();
            long memory = getUsedMemory();
            try (var stream = new ByteArrayInputStream(xml.getBytes(StandardCharsets.UTF_8))) {
                RdfParser.parse(stream, this::createCimObject);
            } catch (Exception ex) {
                String txt = "Error while reading xml data";
                LOG.error(txt, ex);
                throw new RuntimeException(txt, ex);
            }
            memory = getUsedMemory() - memory;
            LOG.info(String.format("Read %d CIM objects using %d MByte (%d)", model.size() - count,
                    memory / (1024 * 1024), memory));
        }
        setAttributeLinks();
        return model;
    }

    private void createCimObject(RdfParser.Element element) {
        var className = element.name.getLocalPart();
        if (element.id != null) {
            if (CimClassMap.isCimClass(className)) {
                BaseClass object = model.get(element.id);
                if (object == null) {
                    object = createNewObject(className, element.id);
                    model.put(element.id, object);
                } else if (!object.getCimType().equals(className)) {
                    BaseClass newObject = retypeObject(object, className, element.id);
                    if (newObject != null) {
                        object = newObject;
                        model.put(element.id, object);
                    } else {
                        LOG.debug(String.format("Found %s (instead of %s) with rdf:ID: %s in map", object.getCimType(),
                                className, element.id));
                    }
                }

                // Set attributes of new object
                for (RdfParser.Attribute attribute : element.attributes) {
                    setAttribute(object, attribute);
                }

            } else {
                LOG.warn(String.format("Unknown CIM class: %s (rdf:ID: %s)", className, element.id));
            }
        } else {
            LOG.warn(String.format("Possible CIM class: %s (rdf:ID missing)", className));
        }
    }

    private BaseClass createNewObject(String className, String rdfid) {
        BaseClass object = CimClassMap.createCimObject(className, rdfid);
        LOG.debug(String.format("Created object of type: %s with rdf:ID: %s", className, rdfid));
        return object;
    }

    private BaseClass retypeObject(BaseClass oldObject, String className, String rdfid) {
        BaseClass newObject = createNewObject(className, rdfid);
        var oldType = oldObject.getClass();
        var newType = newObject.getClass();
        if (oldType.isAssignableFrom(newType)) {
            LOG.debug(String.format("Retyping object with rdf:ID: %s from type: %s to type: %s", rdfid,
                    oldObject.getCimType(), className));

            // Copy attributes from old object to the new object
            for (String attrName : oldObject.getAttributeNames()) {
                Object attr = oldObject.getAttribute(attrName);
                if (attr != null) {
                    if (oldObject.isPrimitiveAttribute(attrName) || oldObject.isEnumAttribute(attrName)) {
                        newObject.setAttribute(attrName, attr);
                    } else if (attr instanceof String) {
                        newObject.setAttribute(attrName, (String) attr);
                    } else if (attr instanceof Set<?>) {
                        for (var attrItem : ((Set<?>) attr)) {
                            if (attrItem instanceof String) {
                                newObject.setAttribute(attrName, (String) attrItem);
                            }
                        }
                    }
                }
            }
            return newObject;
        }
        return null;
    }

    private void setAttribute(BaseClass object, RdfParser.Attribute attribute) {
        var attributeName = attribute.name.getLocalPart();
        if (attributeName.contains(".")) {
            attributeName = attributeName.substring(attributeName.lastIndexOf('.') + 1);
        }
        if (attribute.resource != null) {
            if (!object.getAttributeNames().contains(attributeName)) {
                LOG.error(String.format("Unknown attribute %s with resource %s", attribute.name.getLocalPart(),
                        attribute.resource));
            } else if (!object.isEnumAttribute(attributeName)) {
                // Set only rdfid as attribute - link to object later
                object.setAttribute(attributeName, attribute.resource);
            } else {
                // Set enum attributes
                object.setAttribute(attributeName, attribute.resource);
            }
        } else {
            // Set primitive attributes (including datatype_attributes)
            object.setAttribute(attributeName, attribute.value);
        }
    }

    private void setAttributeLinks() {
        // Set class or list attributes as links to objects
        for (String rdfid : model.keySet()) {
            BaseClass cimObj = model.get(rdfid);
            var attrNames = cimObj.getAttributeNames();
            for (String attrName : attrNames) {
                if (!cimObj.isPrimitiveAttribute(attrName) && !cimObj.isEnumAttribute(attrName)) {
                    Object attr = cimObj.getAttribute(attrName);
                    if (attr instanceof String) {
                        BaseClass attrObj = model.get((String) attr);
                        if (attrObj != null) {
                            try {
                                cimObj.setAttribute(attrName, attrObj);
                            } catch (IllegalArgumentException ex) {
                                LOG.error(String.format("Cannot set attribute %s with attribute object: %s", attrName,
                                        attrObj), ex);
                            }
                        } else {
                            LOG.warn(String.format("Cannot find object with rdf:ID: %s", attr));
                        }
                    } else if (attr instanceof Set<?>) {
                        for (var attrItem : ((Set<?>) attr)) {
                            if (attrItem instanceof String) {
                                BaseClass attrObj = model.get((String) attrItem);
                                if (attrObj != null) {
                                    try {
                                        cimObj.setAttribute(attrName, attrObj);
                                    } catch (IllegalArgumentException ex) {
                                        LOG.error(String.format("Cannot set attribute %s with attribute object: %s",
                                                attrName, attrObj), ex);
                                    }
                                } else {
                                    LOG.warn(String.format("Cannot find object with rdf:ID: %s", attrItem));
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    private long getUsedMemory() {
        Runtime.getRuntime().gc();
        return Runtime.getRuntime().totalMemory() - Runtime.getRuntime().freeMemory();
    }
}
