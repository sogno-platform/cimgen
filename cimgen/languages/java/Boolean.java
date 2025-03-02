package cim4j;

/**
 * A type with the value space "true" and "false".
 */
public class Boolean extends BaseClass {

    private boolean value = false;

    private boolean initialized = false;

    public Boolean() {
    }

    public Boolean(boolean v) {
        value = v;
        initialized = true;
    }

    public Boolean(java.lang.String s) {
        setValue(s);
    }

    @Override
    public BaseClass construct() {
        return new Boolean();
    }

    @Override
    public boolean isPrimitive() {
        return true;
    }

    @Override
    public boolean isInitialized() {
        return initialized;
    }

    @Override
    public void setValue(java.lang.String s) {
        java.lang.String s_ignore_case = s.toLowerCase();
        value = (s_ignore_case.equals("true"));
        initialized = true;
    }

    @Override
    public Object getValue() {
        return java.lang.Boolean.valueOf(value);
    }

    @Override
    public void setAttribute(java.lang.String attrName, BaseClass value) {
        throw new IllegalArgumentException("Boolean class cannot set attribute: " + attrName);
    }

    @Override
    public void setAttribute(java.lang.String attrName, java.lang.String value) {
        throw new IllegalArgumentException("Boolean class cannot set attribute: " + attrName);
    }

    @Override
    public java.lang.String toString(boolean topClass) {
        return java.lang.Boolean.toString(value);
    }

    private final java.lang.String debugName = "Boolean";

    @Override
    public java.lang.String debugString() {
        return debugName;
    }
}
