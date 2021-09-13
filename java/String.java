package cim4j;

import java.util.Map;
import java.util.HashMap;

/**
 * A type with the value space "true" and "false".
 */
public class String extends BaseClass {

	public String(){}
	
	public String(java.lang.String s) {
		setValue(s);
	}
	
	public BaseClass construct() {
		return new String();
        }

	private java.lang.String debugName = "String";

	public java.lang.String debugString()
	{
		return debugName;
	}
	
	public void setAttribute(java.lang.String attributeName, java.lang.String value) {
		setValue(value);
	}

	public void setValue(java.lang.String s) {
	        value = s;
		initialized = true;
        }

	java.lang.String value = "";
	boolean initialized = false;

	public void setAttribute(java.lang.String attributeName, BaseClass value) {
		throw new IllegalArgumentException("String class cannot set attribute: " + attributeName);
	}

	public java.lang.String toString(boolean b) {
		return value;
	}
};
