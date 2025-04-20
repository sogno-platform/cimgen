package cim4j;

import java.util.Set;

public interface BaseClassInterface {

    boolean isPrimitive();

    boolean isInitialized();

    void setValue(java.lang.String s);

    Object getValue();

    void setRdfid(java.lang.String id);

    java.lang.String getRdfid();

    java.lang.String toString(boolean topClass);

    java.lang.String debugString();

    /**
     * Get the namespace URL of an object of this class.
     *
     * @return The namespace URL
     */
    java.lang.String getClassNamespaceUrl();

    /**
     * A resource can be used by multiple profiles. This is the set of profiles
     * where this element can be found.
     *
     * @return All possible profiles for an object of this class
     */
    Set<CGMESProfile> getPossibleProfiles();

    /**
     * This is the profile with most of the attributes.
     * It should be used to write the data to as few as possible files.
     *
     * @return The recommended profiles for an object of this class
     */
    CGMESProfile getRecommendedProfile();

    /**
     * Get the possible profiles for an object of this class including the possible
     * profiles of all direct or inherited attributes.
     *
     * A resource can be used by multiple profiles. This is the set of profiles
     * where this element or an attribute of this element can be found.
     *
     * @return All possible profiles for an object of this class and its attributes
     */
    Set<CGMESProfile> getPossibleProfilesIncludingAttributes();
}
