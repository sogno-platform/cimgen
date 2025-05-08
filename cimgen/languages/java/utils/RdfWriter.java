package cim4j.utils;

import java.io.BufferedWriter;
import java.io.FileWriter;
import java.io.StringWriter;
import java.io.Writer;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Collections;
import java.util.HashMap;
import java.util.HashSet;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Objects;
import java.util.Set;

import javax.xml.stream.XMLOutputFactory;

import cim4j.BaseClass;
import cim4j.CGMESProfile;
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
     * All CIM objects are written to just one file, regardless of profiles.
     *
     * @param path Path of the file to write
     */
    public void write(String path) {
        write(path, null, null, null);
    }

    /**
     * Write the CIM data to RDF files separated by profiles.
     *
     * Each CIM object will be written to its corresponding profile file depending
     * on classProfileMap. But some objects to more than one file if some attribute
     * profiles are not the same as the class profile.
     *
     * @param pathStem        Stem of the output files, resulting files:
     *                        <pathStem>_<profileName>.xml
     * @param modelIdStem     Stem of the model IDs, resulting IDs:
     *                        <modelIdStem>_<profileName>
     * @param classProfileMap Mapping of CIM type to profile
     *
     * @return Written files: Mapping of profile to file
     */
    public Map<CGMESProfile, String> write(String pathStem, String modelIdStem,
            Map<String, CGMESProfile> classProfileMap) {
        Map<CGMESProfile, String> profileToFileMap = new LinkedHashMap<>();

        for (CGMESProfile profile : CGMESProfile.values()) {
            String profileName = profile.getLongName();
            String modelId = modelIdStem + "_" + profileName;
            String path = pathStem + "_" + profileName + ".xml";

            var stringWriter = new StringWriter();
            if (write(stringWriter, profile, modelId, classProfileMap)) {

                try (var writer = new BufferedWriter(new FileWriter(path, StandardCharsets.UTF_8))) {
                    writer.write(stringWriter.toString());
                } catch (Exception ex) {
                    String txt = "Failed to write rdf file";
                    LOG.error(txt, ex);
                    throw new RuntimeException(txt, ex);
                }
                profileToFileMap.put(profile, path);
            }
        }
        return profileToFileMap;
    }

    /**
     * Write the CIM data to a stream (e.g. a file stream).
     *
     * All CIM objects are written to just one stream, regardless of profiles.
     *
     * @param streamWriter Writer to an output stream
     */
    public void write(Writer streamWriter) {
        write(streamWriter, null, null, null);
    }

    /**
     * Write the CIM data corresponding to one profile to a RDF file.
     *
     * If no profile is specified, all objects are written, regardless of profiles.
     * In this case, modelId and classProfileMap are not required.
     *
     * @param path            Path of file to write
     * @param profile         Only data for this profile should be written
     *                        (if specified)
     * @param modelId         Stem of the model IDs, resulting IDs:
     *                        <modelId>_<profileName>
     * @param classProfileMap Mapping of CIM type to profile
     */
    public void write(String path, CGMESProfile profile, String modelId, Map<String, CGMESProfile> classProfileMap) {
        try (var writer = new BufferedWriter(new FileWriter(path, StandardCharsets.UTF_8))) {
            write(writer, profile, modelId, classProfileMap);
        } catch (Exception ex) {
            String txt = "Failed to write rdf file";
            LOG.error(txt, ex);
            throw new RuntimeException(txt, ex);
        }
    }

    /**
     * Write the CIM data corresponding to one profile to a stream
     * (e.g. a file stream).
     *
     * If no profile is specified, all objects are written, regardless of profiles.
     * In this case, modelId and classProfileMap are not required.
     *
     * @param streamWriter    Writer to an output stream
     * @param profile         Only data for this profile should be written
     *                        (if specified)
     * @param modelId         Stem of the model IDs, resulting IDs:
     *                        <modelId>_<profileName>
     * @param classProfileMap Mapping of CIM type to profile
     *
     * @return Success: at least one object is written to the stream
     */
    public boolean write(Writer streamWriter, CGMESProfile profile, String modelId,
            Map<String, CGMESProfile> classProfileMap) {
        final String RDF = CimConstants.NAMESPACES_MAP.get("rdf");
        final String MD = CimConstants.NAMESPACES_MAP.get("md");

        try {
            var factory = XMLOutputFactory.newInstance();
            var writer = factory.createXMLStreamWriter(streamWriter);

            writer.writeStartDocument("utf-8", "1.0");
            writer.writeCharacters("\n");

            var usedNamespaces = getUsedNamespaces();
            if (profile != null) {
                usedNamespaces.put("md", MD);
            }
            var nsList = new ArrayList<>(usedNamespaces.keySet());
            Collections.sort(nsList);

            for (var ns : nsList) {
                writer.setPrefix(ns, usedNamespaces.get(ns));
            }

            writer.writeStartElement(RDF, "RDF");

            for (var ns : nsList) {
                writer.writeNamespace(ns, usedNamespaces.get(ns));
            }

            if (profile != null) {
                writer.writeCharacters("\n  ");
                writer.writeStartElement(MD, "FullModel");
                writer.writeAttribute(RDF, "about", "#" + modelId);
                for (var uri : profile.getUris()) {
                    writer.writeCharacters("\n    ");
                    writer.writeStartElement(MD, "Model.profile");
                    writer.writeCharacters(uri);
                    writer.writeEndElement();
                }
                writer.writeCharacters("\n  ");
                writer.writeEndElement();
            }

            int count = 0;
            for (String rdfid : cimData.keySet()) {
                BaseClass cimObj = cimData.get(rdfid);
                if (!cimObj.getClass().equals(IdentifiedObject.class)
                        && (profile == null || isClassMatchingProfile(cimObj, profile))) {
                    String cimType = cimObj.getCimType();
                    var classProfile = profile != null ? classProfileMap.get(cimType) : null;
                    boolean mainEntryOfObject = Objects.equals(classProfile, profile);

                    var attrNames = cimObj.getAttributeNames();
                    boolean noAttrFound = true;
                    for (String attrName : attrNames) {
                        String attr = cimObj.getAttribute(attrName);
                        if (attr != null && cimObj.isUsedAttribute(attrName) && (profile == null
                                || getAttributeProfile(cimObj, attrName, classProfile) == profile)) {
                            noAttrFound = false;
                            break;
                        }
                    }
                    if (!mainEntryOfObject && noAttrFound) {
                        continue;
                    }

                    writer.writeCharacters("\n  ");
                    writer.writeStartElement(cimObj.getClassNamespaceUrl(), cimType);
                    if (mainEntryOfObject) {
                        writer.writeAttribute(RDF, "ID", rdfid);
                    } else {
                        writer.writeAttribute(RDF, "about", "#" + rdfid);
                    }

                    for (String attrName : attrNames) {
                        var namespaceUrl = cimObj.getAttributeNamespaceUrl(attrName);
                        String attrFullName = cimObj.getAttributeFullName(attrName);
                        String attr = cimObj.getAttribute(attrName);
                        if (attr != null && cimObj.isUsedAttribute(attrName) && (profile == null
                                || getAttributeProfile(cimObj, attrName, classProfile) == profile)) {
                            if (cimObj.isPrimitiveAttribute(attrName)) {
                                writer.writeCharacters("\n    ");
                                writer.writeStartElement(namespaceUrl, attrFullName);
                                writer.writeCharacters(attr);
                                writer.writeEndElement();
                            } else if (cimObj.isEnumAttribute(attrName)) {
                                if (!attr.contains("#")) {
                                    attr = "#" + attr;
                                } else if (attr.indexOf("#") != 0) {
                                    String[] parts = attr.split("#");
                                    attr = namespaceUrl + parts[1];
                                }
                                writer.writeCharacters("\n    ");
                                writer.writeEmptyElement(namespaceUrl, attrFullName);
                                writer.writeAttribute(RDF, "resource", attr);
                            } else {
                                for (var reference : attr.split(" ")) {
                                    writer.writeCharacters("\n    ");
                                    writer.writeEmptyElement(namespaceUrl, attrFullName);
                                    writer.writeAttribute(RDF, "resource", "#" + reference);
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
            return count != 0;
        } catch (Exception ex) {
            throw new RuntimeException("Error while writing RDF/XML data", ex);
        }
    }

    /**
     * Check if this profile is a possible profile for this CIM object.
     *
     * The profile could be the main profile of the type, or the type contains
     * attributes for this profile.
     *
     * For most classes all profiles are matching because of the attributes
     * inherited from IdentifiedObject (e.g. name).
     *
     * @param cimObj  CIM object to get the CIM type from
     * @param profile Profile to check
     *
     * @return True/False
     */
    public static final boolean isClassMatchingProfile(BaseClass cimObj, CGMESProfile profile) {
        if (cimObj.getPossibleProfilesIncludingAttributes().contains(profile)) {
            return true;
        }
        return false;
    }

    /**
     * Get the main profile of this CIM object.
     *
     * Returns the recommended profile of the CIM type.
     *
     * If the type contains attributes for different profiles not all data of the
     * object could be written into one file. To write the data to as few as
     * possible files the main profile should be that with most of the attributes.
     * But some types contain a lot of rarely used special attributes, i.e.
     * attributes for a special profile (e.g. TopologyNode has many attributes for
     * TopologyBoundary, but the main profile should be Topology). That's why
     * attributes that only belong to one profile are skipped in the search
     * algorithm.
     *
     * @param cimObj CIM object to get the CIM type from
     *
     * @return Main profile
     */
    public static final CGMESProfile getClassProfile(BaseClass cimObj) {
        return cimObj.getRecommendedProfile();
    }

    /**
     * Get the main profiles for a list of CIM objects.
     *
     * Searches for the main profile of each CIM type in the object list
     * (@see getClassProfile for details).
     *
     * The result could be used as parameter for the write functions (@see write).
     * But it is also possible to optimize the mapping manually for some CIM types
     * before calling the write function.
     *
     * @param objList List of CIM objects
     *
     * @return Mapping of CIM type to profile
     */
    public static final Map<String, CGMESProfile> getClassProfileMap(Iterable<BaseClass> objList) {
        Map<String, CGMESProfile> profileMap = new LinkedHashMap<>();
        for (BaseClass cimObj : objList) {
            String type = cimObj.getCimType();
            if (!profileMap.containsKey(type)) {
                profileMap.put(type, getClassProfile(cimObj));
            }
        }
        return profileMap;
    }

    /**
     * Get the main profiles for the CIM objects of this writer.
     *
     * @return Mapping of CIM type to profile
     */
    public Map<String, CGMESProfile> getClassProfileMap() {
        return getClassProfileMap(cimData.values());
    }

    /**
     * Get the profile for this attribute of the CIM object.
     *
     * Searches for the profile of an attribute for the CIM type of an object.
     * If the main profile of the type is a possible profile of the attribute
     * it should be choosen. Otherwise, the first profile in the list of possible
     * profiles ordered by profile number.
     *
     * @param cimObj       CIM object to get the CIM type from
     * @param attrName     Attribute to check
     * @param classProfile Main profile of the CIM type
     *
     * @return Attribute profile
     */
    public static final CGMESProfile getAttributeProfile(BaseClass cimObj, String attrName, CGMESProfile classProfile) {
        var profiles = cimObj.getPossibleAttributeProfiles(attrName);
        if (profiles != null && profiles.contains(classProfile)) {
            return classProfile;
        }
        if (profiles != null && !profiles.isEmpty()) {
            var list = new ArrayList<CGMESProfile>(profiles);
            Collections.sort(list);
            return list.get(0);
        }
        return null;
    }

    private Map<String, String> getUsedNamespaces() {
        Set<String> urls = new HashSet<>();
        urls.add(CimConstants.NAMESPACES_MAP.get("rdf"));
        for (String rdfid : cimData.keySet()) {
            BaseClass cimObj = cimData.get(rdfid);
            urls.add(cimObj.getClassNamespaceUrl());
            var attrNames = cimObj.getAttributeNames();
            for (String attrName : attrNames) {
                String attr = cimObj.getAttribute(attrName);
                if (attr != null && cimObj.isUsedAttribute(attrName)) {
                    urls.add(cimObj.getAttributeNamespaceUrl(attrName));
                }
            }
        }
        Map<String, String> namespaces = new HashMap<>();
        for (var url : urls) {
            var ns = getNamespaceKey(url);
            if (ns != null) {
                namespaces.put(ns, url);
            }
        }
        return namespaces;
    }

    private String getNamespaceKey(String url) {
        for (var entry : CimConstants.NAMESPACES_MAP.entrySet()) {
            if (entry.getValue().equals(url)) {
                return entry.getKey();
            }
        }
        return null;
    }
}
