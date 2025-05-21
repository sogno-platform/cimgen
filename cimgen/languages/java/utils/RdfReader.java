package cim4j.utils;

import java.io.ByteArrayInputStream;
import java.io.FileInputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
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
    private final Map<String, List<SetAttribute>> setAttributeMap = new LinkedHashMap<>();
    private final Map<String, BaseClass> replaceMap = new LinkedHashMap<>();

    /**
     * Read the CIM data from a list of RDF files.
     *
     * @param pathList List of files to read
     * @return CIM data as map of rdfid to CIM object
     */
    public Map<String, BaseClass> read(List<String> pathList) {
        model.clear();
        setAttributeMap.clear();
        for (String path : pathList) {
            try (var stream = new FileInputStream(path)) {
                RdfParser.parse(stream, this::createCimObject);
            } catch (Exception ex) {
                String txt = "Error while reading rdf file: " + path;
                LOG.error(txt, ex);
                throw new RuntimeException(txt, ex);
            }
        }
        setRemainingAttributes();
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
        setAttributeMap.clear();
        for (String xml : xmlList) {
            try (var stream = new ByteArrayInputStream(xml.getBytes(StandardCharsets.UTF_8))) {
                RdfParser.parse(stream, this::createCimObject);
            } catch (Exception ex) {
                String txt = "Error while reading xml data";
                LOG.error(txt, ex);
                throw new RuntimeException(txt, ex);
            }
        }
        setRemainingAttributes();
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
                    } else if (attr instanceof BaseClass) {
                        newObject.setAttribute(attrName, attr);
                        removeObjectInAttributeObject((BaseClass) attr, oldObject);
                    } else if (attr instanceof Set<?>) {
                        for (var attrObject : ((Set<?>) attr)) {
                            newObject.setAttribute(attrName, attrObject);
                        }
                    }
                }
            }

            // for use in setRemainingAttributes
            replaceMap.put(oldObject.getRdfid(), newObject);

            return newObject;
        }
        return null;
    }

    private void removeObjectInAttributeObject(BaseClass attrObject, BaseClass oldObject) {
        for (String attrName : attrObject.getAttributeNames()) {
            Object attr = attrObject.getAttribute(attrName);
            if (attr instanceof Set<?> && ((Set<?>) attr).contains(oldObject)) {
                ((Set<?>) attr).remove(oldObject);
            }
        }
    }

    private void setAttribute(BaseClass object, RdfParser.Attribute attribute) {
        var attributeName = attribute.name.getLocalPart();
        if (attributeName.contains(".")) {
            attributeName = attributeName.substring(attributeName.lastIndexOf('.') + 1);
        }
        if (attribute.resource != null) {
            if (!object.isEnumAttribute(attributeName)) {
                if (model.containsKey(attribute.resource)) {
                    // Set class attribute as link to an already existng object
                    BaseClass attributeObject = model.get(attribute.resource);
                    object.setAttribute(attributeName, attributeObject);
                } else {
                    // Set attribute later in setRemainingAttributes
                    var setAttribute = new SetAttribute(attributeName, object);
                    setAttributeMap.computeIfAbsent(attribute.resource, k -> new ArrayList<>()).add(setAttribute);
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

    private void setRemainingAttributes() {
        for (var resource : setAttributeMap.keySet()) {
            var setAttributeList = setAttributeMap.get(resource);
            BaseClass attributeObject = model.get(resource);
            if (attributeObject != null) {
                for (var setAttribute : setAttributeList) {
                    var object = setAttribute.object;
                    if (replaceMap.containsKey(object.getRdfid())) {
                        object = replaceMap.get(object.getRdfid());
                    }
                    object.setAttribute(setAttribute.name, attributeObject);
                }
            } else {
                LOG.warn(String.format("Cannot find object with rdf:ID: %s", resource));
            }
        }
    }

    public static class SetAttribute {
        public SetAttribute(String n, BaseClass o) {
            name = n;
            object = o;
        }

        public String name;
        public BaseClass object;
    }
}
