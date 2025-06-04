package cim4j.utils;

import java.io.ByteArrayInputStream;
import java.io.FileInputStream;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.HashSet;
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
    private final List<SetAttribute> setAttributeList = new ArrayList<>();
    private final Map<BaseClass, Set<String>> allowOverrideMap = new LinkedHashMap<>();
    private final Map<String, BaseClass> replaceMap = new LinkedHashMap<>();

    /**
     * Read the CIM data from a list of RDF files.
     *
     * @param pathList List of files to read
     * @return CIM data as map of rdfid to CIM object
     */
    public Map<String, BaseClass> read(List<String> pathList) {
        model.clear();
        setAttributeList.clear();
        allowOverrideMap.clear();
        replaceMap.clear();
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
        long memory = getUsedMemory();
        setRemainingAttributes();
        memory = getUsedMemory() - memory;
        LOG.info(String.format("Set remaining %d attributes using %d MByte (%d)", setAttributeList.size(),
                memory / (1024 * 1024), memory));
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
        setAttributeList.clear();
        allowOverrideMap.clear();
        replaceMap.clear();
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
        long memory = getUsedMemory();
        setRemainingAttributes();
        memory = getUsedMemory() - memory;
        LOG.info(String.format("Set remaining attributes using %d MByte (%d)", memory / (1024 * 1024), memory));
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
            if (!object.getAttributeNames().contains(attributeName)) {
                LOG.error(String.format("Unknown attribute %s with resource %s", attribute.name.getLocalPart(),
                        attribute.resource));
            } else if (!object.isEnumAttribute(attributeName)) {
                boolean setLater = false;
                if (model.containsKey(attribute.resource)) {
                    // Set class or list attribute as link to an already existing object
                    BaseClass attributeObject = model.get(attribute.resource);
                    try {
                        object.setAttribute(attributeName, attributeObject);
                    } catch (IllegalArgumentException ex) {
                        setLater = true;
                    }
                } else {
                    setLater = true;
                }
                if (setLater) {
                    // Set attribute later in setRemainingAttributes
                    var setAttribute = new SetAttribute(object, attributeName, attribute.resource);
                    setAttributeList.add(setAttribute);
                    // Allow override of class attribute in setRemainingAttributes
                    if (object.getAttribute(attributeName) instanceof BaseClass) {
                        allowOverrideMap.computeIfAbsent(object, k -> new HashSet<>()).add(attributeName);
                    }
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
        Map<BaseClass, Map<String, BaseClass>> classAttributeMap = new LinkedHashMap<>();
        for (var setAttribute : setAttributeList) {
            BaseClass attributeObject = model.get(setAttribute.resource);
            if (attributeObject != null) {
                var object = setAttribute.object;
                if (replaceMap.containsKey(object.getRdfid())) {
                    object = replaceMap.get(object.getRdfid());
                }
                var attr = object.getAttribute(setAttribute.name);
                if (attr instanceof Set<?>) {
                    // For list attributes all found links should be set.
                    object.setAttribute(setAttribute.name, attributeObject);
                } else if (!(attr instanceof BaseClass) || (allowOverrideMap.containsKey(object)
                        && allowOverrideMap.get(object).contains(setAttribute.name))) {
                    // For class attributes only the last found link should be set.
                    // But only if the link is not set before setRemainingAttributes.
                    classAttributeMap.computeIfAbsent(object, k -> new LinkedHashMap<>()).put(setAttribute.name,
                            attributeObject);
                }
            } else {
                LOG.error(String.format("Cannot find object with rdf:ID: %s", setAttribute.resource));
            }
        }
        for (var object : classAttributeMap.keySet()) {
            for (var entry : classAttributeMap.get(object).entrySet()) {
                var attributeName = entry.getKey();
                var attributeObject = entry.getValue();
                try {
                    object.setAttribute(attributeName, attributeObject);
                } catch (IllegalArgumentException ex) {
                    LOG.error(String.format("Cannot set attribute %s with object: %s", attributeName, attributeObject),
                            ex);
                }
            }
        }
    }

    private long getUsedMemory() {
        Runtime.getRuntime().gc();
        return Runtime.getRuntime().totalMemory() - Runtime.getRuntime().freeMemory();
    }

    public static class SetAttribute {
        public SetAttribute(BaseClass o, String n, String r) {
            object = o;
            name = n;
            resource = r;
        }

        public BaseClass object;
        public String name;
        public String resource;
    }
}
