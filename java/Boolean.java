package cim4j;

import java.util.Map;
import java.util.HashMap;

/**
 * A type with the value space "true" and "false".
 */
public class Boolean extends BaseClass {

	public Boolean(){}
	
	public Boolean(boolean v) {
	        value = v;
		initialized = true;
	}
	
	public Boolean(java.lang.String s) {
		setValue(s);
	}
	
	public BaseClass construct() {
		return new Boolean();
        }

	private java.lang.String debugName = "Boolean";

	public java.lang.String debugString()
	{
		return debugName;
	}
	
	public void setAttribute(java.lang.String attributeName, java.lang.String value) {
		setValue(value);
	}

	public void setValue(java.lang.String s) {
                java.lang.String s_ignore_case = s.toLowerCase();
	        value = (s == "true");
		initialized = true;
        }

	boolean value = false;
	boolean initialized = false;

	public void setAttribute(java.lang.String attributeName, BaseClass value) {
		throw new IllegalArgumentException("Boolean class cannot set attribute: " + attributeName);
	}

	public java.lang.String toString() {
		return java.lang.Boolean.toString(value);
	}
};
