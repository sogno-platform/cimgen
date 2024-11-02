package cim4j;


public abstract class BaseClass implements BaseClassInterface, BaseClassBuilder, AttributeInterface {

	@Override
	public void setRdfid(java.lang.String id) {
		System.out.println("Shouldn't have instantiated an abstract class: " + id);
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
	public java.lang.String toString(boolean topClass) {
		return "";
	}
}
