
package cim4j;

import java.util.Map;
import java.util.HashMap;

public abstract class BaseClass implements BaseClassBuilder, AttributeInterface {

	public abstract BaseClass construct();

	public void setRdfid(java.lang.String s) {
		System.out.println("Shouldn't have instantiated an abstract class: " + s);
	}

	public void setAttribute(java.lang.String s, BaseClass v) {
		System.out.println("No-one knows what to do with the attribute: " + s);
	}

	public void setAttribute(java.lang.String s, java.lang.String v) {
		System.out.println("No-one knows what to do with the attribute: " + s);
	}

	public abstract java.lang.String debugString();

	public java.lang.String listAttributes() {
		return "";
	}

	public java.lang.String toString(boolean b) {
		return "";
	}
};

