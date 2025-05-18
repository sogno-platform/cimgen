package cim4j;

import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.function.BiConsumer;
import java.util.function.Function;

/**
 * Base class of the CIM type hierarchy - all not primitive CIM classes inherit
 * from this class.
 *
 * The rdfid is a unique identifier inside of a CIM model.
 * The cimType is the name of the real class of the CIM object - a subclass of
 * BaseClass.
 * The rdfid and cimType are fixed after creation of a CIM object.
 */
public abstract class BaseClass {

    private static final Logging LOG = Logging.getLogger(BaseClass.class);

    /**
     * Constructor for subclasses.
     *
     * @param cimType The name of the CIM type.
     * @param rdfid   The RDF ID of the CIM object read from rdf:ID or rdf:about.
     */
    protected BaseClass(String cimType, String rdfid) {
        this.cimType = cimType;
        this.rdfid = rdfid;
    }

    /**
     * The name of the CIM type.
     */
    private String cimType;

    public String getCimType() {
        return cimType;
    }

    /**
     * The RDF ID of the CIM object read from rdf:ID or rdf:about.
     */
    private String rdfid;

    public String getRdfid() {
        return rdfid;
    }

    /**
     * Indicates whether some other object is "equal to" this one.
     *
     * @param obj  the reference object with which to compare.
     * @return     true if this object is the same as the obj argument; false otherwise.
     */
    @Override
    public final boolean equals(Object obj) {
        if (obj == this)
            return true;
        if (obj == null || obj.getClass() != getClass())
            return false;
        BaseClass other = (BaseClass) obj;
        if (rdfid == null ? other.rdfid != null : !rdfid.equals(other.rdfid))
            return false;
        return true;
    }

    /**
     * Returns a hash code value for the object.
     *
     * This method is supported for the benefit of hash tables such as those
     * provided by HashMap.
     *
     * @return  a hash code value for this object.
     */
    @Override
    public final int hashCode() {
        final int PRIME = 31;
        int result = 1;
        result = (result * PRIME) + (rdfid == null ? 0 : rdfid.hashCode());
        return result;
    }

    /**
     * Get a list of all attribute names of the CIM type.
     *
     * The list includes all inherited attributes. The attribute name is only the
     * last part of the full name (without the class name).
     *
     * @return All attributes of the CIM type
     */
    public abstract List<String> getAttributeNames();

    protected Map<String, AttrDetails> allAttrDetailsMap() {
        return Map.of();
    }

    /**
     * Get the full name of an attribute.
     *
     * The full name is "<class_name>.<attribute_name>".
     *
     * @param attrName The attribute name
     * @return         The full name
     */
    public abstract String getAttributeFullName(String attrName);

    /**
     * Get an attribute value as string.
     *
     * @param attrName The attribute name
     * @return         The attribute value
     */
    public abstract String getAttribute(String attrName);

    /**
     * Set an attribute value as object (for class and list attributes).
     *
     * @param attrName    The attribute name
     * @param objectValue The attribute value as object
     */
    public abstract void setAttribute(String attrName, BaseClass objectValue);

    /**
     * Set an attribute value as string (for primitive (including datatype) and enum attributes).
     *
     * @param attrName    The attribute name
     * @param stringValue The attribute value as string
     */
    public abstract void setAttribute(String attrName, String stringValue);

    /**
     * Check if the attribute is a primitive attribute.
     *
     * This includes datatype_attributes.
     *
     * @param attrName The attribute name
     * @return         Is it a primitive attribute?
     */
    public abstract boolean isPrimitiveAttribute(String attrName);

    /**
     * Check if the attribute is an enum attribute.
     *
     * @param attrName The attribute name
     * @return         Is it an enum attribute?
     */
    public abstract boolean isEnumAttribute(String attrName);

    /**
     * Check if the attribute is used.
     *
     * Some attributes are declared as unused in the CGMES definition. In most cases
     * these are list attributes, i.e. lists of links to other CIM objects. But
     * there are some exceptions, e.g. the list of ToplogicalNodes in
     * TopologicalIsland.
     *
     * @param attrName The attribute name
     * @return         Is the attribute used?
     */
    public abstract boolean isUsedAttribute(String attrName);

    /**
     * Get the namespace URL of an object of this class.
     *
     * @return The namespace URL
     */
    public abstract String getClassNamespaceUrl();

    /**
     * Get the namespace URL of an attribute (also for inherited attributes).
     *
     * @return The namespace URL
     */
    public abstract String getAttributeNamespaceUrl(String attrName);

    /**
     * A resource can be used by multiple profiles. This is the set of profiles
     * where this element can be found.
     *
     * @return All possible profiles for an object of this class
     */
    public abstract Set<CGMESProfile> getPossibleProfiles();

    /**
     * This is the profile with most of the attributes.
     * It should be used to write the data to as few as possible files.
     *
     * @return The recommended profiles for an object of this class
     */
    public abstract CGMESProfile getRecommendedProfile();

    /**
     * Get the possible profiles of an attribute (also for inherited attributes).
     *
     * @return All possible profiles for an attribute
     */
    public abstract Set<CGMESProfile> getPossibleAttributeProfiles(String attrName);

    /**
     * Get the possible profiles for an object of this class including the possible
     * profiles of all direct or inherited attributes.
     *
     * A resource can be used by multiple profiles. This is the set of profiles
     * where this element or an attribute of this element can be found.
     *
     * @return All possible profiles for an object of this class and its attributes
     */
    public abstract Set<CGMESProfile> getPossibleProfilesIncludingAttributes();

    /**
     * Helper functions.
     */

    protected Boolean getBooleanFromString(String stringValue) {
        return stringValue.toLowerCase().equals("true");
    }

    protected Double getDoubleFromString(String stringValue) {
        try {
            return Double.valueOf(stringValue);
        } catch (NumberFormatException ex) {
            LOG.error("Error getting Double from String", ex);
            return null;
        }
    }

    protected Float getFloatFromString(String stringValue) {
        try {
            return Float.valueOf(stringValue);
        } catch (NumberFormatException ex) {
            LOG.error("Error getting Float from String", ex);
            return null;
        }
    }

    protected Integer getIntegerFromString(String stringValue) {
        try {
            return Integer.parseInt(stringValue.trim());
        } catch (NumberFormatException ex) {
            LOG.error("Error getting Integer from String", ex);
            return null;
        }
    }

    protected String getStringFromSet(Set<? extends BaseClass> set) {
        if (!set.isEmpty()) {
            String references = "";
            for (var obj : set) {
                references += obj.getRdfid() + " ";
            }
            return references.trim();
        }
        return null;
    }

    /**
     * Nested helper classes.
     */

    protected static class AttrDetails {
        public AttrDetails(String f, boolean u, String n, Set<CGMESProfile> c, boolean p, boolean e,
                Function<BaseClass, String> g, BiConsumer<BaseClass, BaseClass> o, BiConsumer<BaseClass, String> s) {
            fullName = f;
            isUsed = u;
            nameSpace = n;
            profiles = c;
            isPrimitive = p;
            isEnum = e;
            getter = g;
            objectSetter = o;
            stringSetter = s;
        }

        public String fullName;
        public boolean isUsed;
        public String nameSpace;
        public Set<CGMESProfile> profiles;
        public Boolean isPrimitive;
        public Boolean isEnum;
        public Function<BaseClass, String> getter;
        public BiConsumer<BaseClass, BaseClass> objectSetter;
        public BiConsumer<BaseClass, String> stringSetter;
    }
}
