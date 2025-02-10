package cim4j;

import java.util.LinkedHashMap;
import java.util.LinkedHashSet;
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

	/**
	 * Get the namespace URL of an object of this class.
	 *
	 * @return The namespace URL
	 */
	@Override
	public java.lang.String getClassNamespaceUrl() {
		return CimConstants.NAMESPACES_MAP.get("cim");
	}

	/**
	 * Get the namespace URL of an attribute (also for inherited attributes).
	 *
	 * @return The namespace URL
	 */
	@Override
	public java.lang.String getAttributeNamespaceUrl(java.lang.String attrName) {
		return CimConstants.NAMESPACES_MAP.get("cim");
	}

	protected Map<java.lang.String, java.lang.String> allAttrNamespaceMap() {
		Map<java.lang.String, java.lang.String> map = new LinkedHashMap<>();
		return map;
	}
}
