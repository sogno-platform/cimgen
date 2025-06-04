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
    private final HandleSetLater handleSetLater = new HandleSetLater();

    /**
     * Read the CIM data from a list of RDF files.
     *
     * @param pathList List of files to read
     * @return CIM data as map of rdfid to CIM object
     */
    public Map<String, BaseClass> read(List<String> pathList) {
        model.clear();
        handleSetLater.clear();
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
        logRemainingResources();
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
        handleSetLater.clear();
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
        logRemainingResources();
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

                // Set object as link in other objects previously found
                handleSetLater.execute(object);
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

            handleSetLater.replace(oldObject, newObject);
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
                        // Prevent to set the class attribute later
                        if (!(object.getAttribute(attributeName) instanceof Set<?>)) {
                            handleSetLater.remove(object, attributeName);
                        }
                    } catch (IllegalArgumentException ex) {
                        setLater = true;
                    }
                } else {
                    setLater = true;
                }
                if (setLater) {
                    // Set class or list attribute later
                    handleSetLater.add(object, attributeName, attribute.resource);
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

    private void logRemainingResources() {
        for (var resource : handleSetLater.getResources()) {
            BaseClass object = model.get(resource);
            if (object == null) {
                LOG.error(String.format("Cannot find object with rdf:ID: %s", resource));
            } else {
                LOG.error(String.format("Cannot set attributes with attribute object: %s", object));
            }
        }
    }

    private long getUsedMemory() {
        Runtime.getRuntime().gc();
        return Runtime.getRuntime().totalMemory() - Runtime.getRuntime().freeMemory();
    }

    private static class HandleSetLater {
        private final Map<String, Map<String, List<BaseClass>>> resourceNameObjectMap = new LinkedHashMap<>();
        private final Map<BaseClass, Map<String, List<String>>> objectNameResourceMap = new LinkedHashMap<>();

        public void clear() {
            resourceNameObjectMap.clear();
            objectNameResourceMap.clear();
        }

        public void add(BaseClass object, String attrName, String resource) {
            // If its a class attribute remove previously set resources
            if (!(object.getAttribute(attrName) instanceof Set<?>)) {
                remove(object, attrName);
            }

            var nameObjectMap = resourceNameObjectMap.computeIfAbsent(resource, k -> new LinkedHashMap<>());
            nameObjectMap.computeIfAbsent(attrName, k -> new ArrayList<>()).add(object);

            var nameResourceMap = objectNameResourceMap.computeIfAbsent(object, k -> new LinkedHashMap<>());
            nameResourceMap.computeIfAbsent(attrName, k -> new ArrayList<>()).add(resource);
        }

        public void execute(BaseClass object) {
            var resource = object.getRdfid();
            if (resourceNameObjectMap.containsKey(resource)) {
                var removeNameObjectMap = new LinkedHashMap<String, List<BaseClass>>();
                for (var nameAndObjects : resourceNameObjectMap.get(resource).entrySet()) {
                    var attrName = nameAndObjects.getKey();
                    for (var otherObject : nameAndObjects.getValue()) {
                        boolean success = true;
                        try {
                            otherObject.setAttribute(attrName, object);
                        } catch (IllegalArgumentException ex) {
                            success = false;
                        }
                        if (success) {
                            removeNameObjectMap.computeIfAbsent(attrName, k -> new ArrayList<>()).add(otherObject);
                        }
                    }
                }
                for (var attrName : removeNameObjectMap.keySet()) {
                    for (var otherObject : removeNameObjectMap.get(attrName)) {
                        remove(otherObject, attrName, resource);
                    }
                }
            }
        }

        public void remove(BaseClass object, String attrName) {
            var nameResourceMap = objectNameResourceMap.get(object);
            if (nameResourceMap != null && nameResourceMap.containsKey(attrName)) {
                var removeResources = new ArrayList<>(nameResourceMap.get(attrName));
                for (var resource : removeResources) {
                    remove(object, attrName, resource);
                }
            }
        }

        public void replace(BaseClass oldObject, BaseClass newObject) {
            var nameResourceMap = objectNameResourceMap.get(oldObject);
            if (nameResourceMap != null) {
                for (var attrName : nameResourceMap.keySet()) {
                    for (var resource : nameResourceMap.get(attrName)) {
                        var objects = resourceNameObjectMap.get(resource).get(attrName);
                        objects.set(objects.indexOf(oldObject), newObject);
                    }
                }
                objectNameResourceMap.remove(oldObject);
                objectNameResourceMap.put(newObject, nameResourceMap);
            }
        }

        public Set<String> getResources() {
            return resourceNameObjectMap.keySet();
        }

        private void remove(BaseClass object, String attrName, String resource) {
            var nameObjectMap = resourceNameObjectMap.get(resource);
            if (nameObjectMap != null && nameObjectMap.containsKey(attrName)) {
                nameObjectMap.get(attrName).remove(object);
                if (nameObjectMap.get(attrName).isEmpty()) {
                    nameObjectMap.remove(attrName);
                }
                if (nameObjectMap.isEmpty()) {
                    resourceNameObjectMap.remove(resource);
                }
            }
            var nameResourceMap = objectNameResourceMap.get(object);
            if (nameResourceMap != null && nameResourceMap.containsKey(attrName)) {
                nameResourceMap.get(attrName).remove(resource);
                if (nameResourceMap.get(attrName).isEmpty()) {
                    nameResourceMap.remove(attrName);
                }
                if (nameResourceMap.isEmpty()) {
                    objectNameResourceMap.remove(object);
                }
            }
        }
    }
}
