package cim4j; 

import java.util.Map;
import java.lang.Double;
import java.util.HashMap;
import java.lang.IllegalArgumentException;

/**
 * A floating point number. The range is unspecified and not limited.
 */
public class Float extends BaseClass {

	public Float() {}

	public Float(double v) {
		value = v;
		initialized = true;
	}

	public Float(java.lang.String s) {
		setValue(s);
	}

	public BaseClass construct() {
		return new Float();
        }

	public void setAttribute(java.lang.String attributeName, java.lang.String value) {
		setValue(value);
	}

	public void setValue(java.lang.String s) {
		try
		{
			value = java.lang.Float.valueOf(s.trim()).floatValue();
			initialized = true;
		}
		catch (NumberFormatException nfe)
		{
			System.out.println("NumberFormatException: " + nfe.getMessage());
		}
        }

	public double value = 0.0;
	public boolean initialized = false;

	private final java.lang.String debugName = "Float";

	public java.lang.String debugString() {
		return debugName;
	}

	public void setAttribute(java.lang.String attributeName, BaseClass value) {
		throw new IllegalArgumentException("Float class cannot set attribute: " + attributeName);
	}

	public java.lang.String toString() {
		return Double.toString(value);
	}
};

