package cim4j;

import java.util.Map;
import java.util.Set;

public abstract class BaseClass implements BaseClassInterface, BaseClassBuilder, AttributeInterface {

    private static final Logging LOG = Logging.getLogger(BaseClass.class);

    @Override
    public boolean isPrimitive() {
        return false;
    }

    @Override
    public boolean isInitialized() {
        return false;
    }

    @Override
    public Object getValue() {
        return null;
    }

    @Override
    public void setRdfid(java.lang.String id) {
        LOG.error("Shouldn't have instantiated an abstract class: " + id);
    }

    @Override
    public java.lang.String getRdfid() {
        return null;
    }

    @Override
    public void setAttribute(java.lang.String attrName, BaseClass value) {
        LOG.error("No-one knows what to do with the attribute: " + attrName);
    }

    @Override
    public void setAttribute(java.lang.String attrName, java.lang.String value) {
        LOG.error("No-one knows what to do with the attribute: " + attrName);
    }

    @Override
    public BaseClass getAttribute(java.lang.String attrName) {
        return null;
    }

    protected Map<java.lang.String, java.lang.String> getAttributeNamesMap() {
        return Map.of();
    }

    @Override
    public Set<java.lang.String> getAttributeNames() {
        throw new RuntimeException("Method not implemented.");
    }

    @Override
    public java.lang.String getAttributeFullName(java.lang.String attrName) {
        throw new RuntimeException("Method not implemented.");
    }

    @Override
    public java.lang.String toString(boolean topClass) {
        throw new RuntimeException("Method not implemented.");
    }

    /**
     * Get the namespace URL of an object of this class.
     *
     * @return The namespace URL
     */
    @Override
    public java.lang.String getClassNamespaceUrl() {
        throw new RuntimeException("Method not implemented.");
    }

    /**
     * Get the namespace URL of an attribute (also for inherited attributes).
     *
     * @return The namespace URL
     */
    @Override
    public java.lang.String getAttributeNamespaceUrl(java.lang.String attrName) {
        throw new RuntimeException("Method not implemented.");
    }

    protected Map<java.lang.String, AttrDetails> allAttrDetailsMap() {
        return Map.of();
    }

    /**
     * A resource can be used by multiple profiles. This is the set of profiles
     * where this element can be found.
     *
     * @return All possible profiles for an object of this class
     */
    @Override
    public Set<CGMESProfile> getPossibleProfiles() {
        throw new RuntimeException("Method not implemented.");
    }

    /**
     * This is the profile with most of the attributes.
     * It should be used to write the data to as few as possible files.
     *
     * @return The recommended profiles for an object of this class
     */
    @Override
    public CGMESProfile getRecommendedProfile() {
        throw new RuntimeException("Method not implemented.");
    }

    /**
     * Get the possible profiles of an attribute (also for inherited attributes).
     *
     * @return All possible profiles for an attribute
     */
    @Override
    public Set<CGMESProfile> getPossibleAttributeProfiles(java.lang.String attrName) {
        throw new RuntimeException("Method not implemented.");
    }

    /**
     * Get the possible profiles for an object of this class including the possible
     * profiles of all direct or inherited attributes.
     *
     * A resource can be used by multiple profiles. This is the set of profiles
     * where this element or an attribute of this element can be found.
     *
     * @return All possible profiles for an object of this class and its attributes
     */
    @Override
    public Set<CGMESProfile> getPossibleProfilesIncludingAttributes() {
        throw new RuntimeException("Method not implemented.");
    }

    /**
     * Nested helper class.
     */
    protected static class AttrDetails {
        public AttrDetails(java.lang.String n, Set<CGMESProfile> c) {
            nameSpace = n;
            profiles = c;
        }

        public java.lang.String nameSpace;
        public Set<CGMESProfile> profiles;
    }
}
