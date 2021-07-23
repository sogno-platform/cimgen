package cim4j;

import java.util.Map;
import java.util.HashMap;
import cim4j.BaseClass;
import java.lang.IllegalArgumentException;


/*
Date as "yyyy-mm-dd", which conforms with ISO 8601. UTC time zone is specified as "yyyy-mm-ddZ". A local timezone relative UTC is specified as "yyyy-mm-dd(+/-)hh:mm".
*/

public class Date extends BaseClass {
	public Date() {}

	public Date(java.lang.String s) {
		value = s;
	}

	public BaseClass construct() {
		return new Date();
        }

	public void setAttribute(String attributeName, java.lang.String value) {
		setValue(value);
	}

	public void setValue(java.lang.String s) {
	        value = s;
        }

	private java.lang.String value;

	private java.lang.String debugName = "Date";

	public java.lang.String debugString() {
		return debugName;
	}

	public void setAttribute(java.lang.String attributeName, BaseClass value) {
		throw new IllegalArgumentException("Date class cannot set attribute: " + attributeName);
	}

	public java.lang.String toString() {
		return value;
	}
}
