package cim4j;

import java.util.Map;
import java.util.HashMap;
import java.lang.IllegalArgumentException;

/**
* An Integer number. The range is unspecified and not limited.
*/
public class Integer extends BaseClass implements AttributeInterface {

	public int     value = 0;

	public boolean initialized = false;

	public BaseClass construct() {
		return new Float();
        }

	public Integer(){}

	public Integer(int v) {
		value = v;
		initialized = true;
	}

	public Integer(java.lang.String s) {
		setValue(s);
	}

	public void setAttribute(java.lang.String attributeName, java.lang.String value) {
		setValue(value);
	}

	public void setValue(java.lang.String s) {
		try
		{
			value = java.lang.Integer.parseInt(s.trim());
			initialized = true;
		}
		catch (NumberFormatException nfe)
		{
			System.out.println("NumberFormatException: " + nfe.getMessage());
		}
        }

	public java.lang.String debugName = "Integer";

	public java.lang.String debugString() {
		return debugName;
        }

	public void setAttribute(java.lang.String attributeName, BaseClass value) {
		throw new IllegalArgumentException("Integer class cannot set attribute: " + attributeName);
	}

	public java.lang.String toString(boolean b) {
		return java.lang.Integer.toString(value);
	}
};
