package cim4j;

import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
import java.util.Map;
import java.util.Set;

public abstract class BaseClass implements BaseClassInterface, BaseClassBuilder, AttributeInterface {

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
		System.out.println("Shouldn't have instantiated an abstract class: " + id);
	}

	@Override
	public java.lang.String getRdfid() {
		return null;
	}

	@Override
	public void setAttribute(java.lang.String attrName, BaseClass value) {
		System.out.println("No-one knows what to do with the attribute: " + attrName);
	}

	@Override
	public void setAttribute(java.lang.String attrName, java.lang.String value) {
		System.out.println("No-one knows what to do with the attribute: " + attrName);
	}

	@Override
	public BaseClass getAttribute(java.lang.String attrName) {
		return null;
	}

	protected Map<java.lang.String, java.lang.String> getAttributeNamesMap() {
		Map<java.lang.String, java.lang.String> namesMap = new LinkedHashMap<>();
		return namesMap;
	}

	@Override
	public Set<java.lang.String> getAttributeNames() {
		LinkedHashSet<java.lang.String> attrNames = new LinkedHashSet<>();
		return attrNames;
	}

	@Override
	public java.lang.String getAttributeFullName(java.lang.String attrName) {
		return null;
	}

	@Override
	public java.lang.String toString(boolean topClass) {
		return "";
	}
}
