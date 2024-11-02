package cim4j;

import java.util.Set;

public interface AttributeInterface {
	void setAttribute(java.lang.String attrName, BaseClass value);
	void setAttribute(java.lang.String attrName, java.lang.String value);
	BaseClass getAttribute(java.lang.String attrName);
	Set<java.lang.String> getAttributeNames();
	java.lang.String getAttributeFullName(java.lang.String attrName);
}
