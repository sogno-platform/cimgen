package cim4j.utils;

import java.io.ByteArrayInputStream;
import java.io.FileInputStream;
import java.nio.charset.StandardCharsets;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

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
        for (String path : pathList) {
            int count = model.size();
            long memory = getUsedMemory();
            try (var stream = new FileInputStream(path)) {
                RdfParser.parse(stream, this::addAttributes);
            } catch (Exception ex) {
                String txt = "Error while adding attributes read from rdf file: " + path;
                LOG.error(txt, ex);
                throw new RuntimeException(txt, ex);
            }
            memory = getUsedMemory() - memory;
            LOG.info(String.format("Fill %d CIM objects from %s using %d MByte (%d)", model.size() - count,
                    path, memory / (1024 * 1024), memory));
        }
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
        for (String xml : xmlList) {
            int count = model.size();
            long memory = getUsedMemory();
            try (var stream = new ByteArrayInputStream(xml.getBytes(StandardCharsets.UTF_8))) {
                RdfParser.parse(stream, this::addAttributes);
            } catch (Exception ex) {
                String txt = "Error while adding attributes";
                LOG.error(txt, ex);
                throw new RuntimeException(txt, ex);
            }
            memory = getUsedMemory() - memory;
            LOG.info(String.format("Fill %d CIM objects using %d MByte (%d)", model.size() - count,
                    memory / (1024 * 1024), memory));
        }
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
                    BaseClass newObject = createNewObject(className, element.id);
                    var oldType = object.getClass();
                    var newType = newObject.getClass();
                    if (oldType.isAssignableFrom(newType)) {
                        LOG.debug(String.format("Retyping object with rdf:ID: %s from type: %s to type: %s",
                                element.id, object.getCimType(), className));
                        model.put(element.id, newObject);
                    } else {
                        LOG.debug(String.format("Found %s (instead of %s) with rdf:ID: %s in map", object.getCimType(),
                                className, element.id));
                    }
                }
            } else {
                LOG.warn(String.format("Unknown CIM class: %s (rdf:ID: %s)", className, element.id));
            }
        } else {
            LOG.warn(String.format("Possible CIM class: %s (rdf:ID missing)", className));
        }
    }

    private void addAttributes(RdfParser.Element element) {
        if (element.id != null && model.containsKey(element.id)) {
            BaseClass object = model.get(element.id);

            // Set attributes of new object
            for (RdfParser.Attribute attribute : element.attributes) {
                setAttribute(object, attribute);
            }
        }
    }

    private BaseClass createNewObject(String className, String rdfid) {
        BaseClass object = CimClassMap.createCimObject(className, rdfid);
        LOG.debug(String.format("Created object of type: %s with rdf:ID: %s", className, rdfid));
        return object;
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
                if (model.containsKey(attribute.resource)) {
                    // Set class or list attribute as link to an already existing object
                    BaseClass attributeObject = model.get(attribute.resource);
                    try {
                        object.setAttribute(attributeName, attributeObject);
                    } catch (IllegalArgumentException ex) {
                        LOG.error(String.format("Cannot set attribute %s with attribute object: %s", attributeName,
                                attributeObject), ex);
                    }
                } else {
                    LOG.error(String.format("Cannot find object with rdf:ID: %s", attribute.resource));
                }
            } else {
                // Set enum attributes
                object.setAttribute(attributeName, attribute.resource);
            }
        } else {
            // Set primitive attributes (including datatype_attributes)
            object.setAttribute(attributeName, attribute.value);
        }
    }

    private long getUsedMemory() {
        Runtime.getRuntime().gc();
        return Runtime.getRuntime().totalMemory() - Runtime.getRuntime().freeMemory();
    }
}
