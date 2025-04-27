package cim4j;

import java.util.Set;

public interface AttributeInterface {

    void setAttribute(java.lang.String attrName, BaseClass value);

    void setAttribute(java.lang.String attrName, java.lang.String value);

    BaseClass getAttribute(java.lang.String attrName);

    /**
     * Get a list of all attribute names of the CIM type.
     *
     * The list includes all inherited attributes. The attribute name is only the
     * last part of the full name (without the class name).
     *
     * @return All attributes of the CIM type
     */
    Set<java.lang.String> getAttributeNames();

    /**
     * Get the full name of an attribute.
     *
     * The full name is "<class_name>.<attribute_name>".
     *
     * @param attrName The attribute name
     * @return         The full name
     */
    java.lang.String getAttributeFullName(java.lang.String attrName);

    /**
     * Get the namespace URL of an attribute (also for inherited attributes).
     *
     * @return The namespace URL
     */
    java.lang.String getAttributeNamespaceUrl(java.lang.String attrName);

    /**
     * Get the possible profiles of an attribute (also for inherited attributes).
     *
     * @return All possible profiles for an attribute
     */
    Set<CGMESProfile> getPossibleAttributeProfiles(java.lang.String attrName);
}
