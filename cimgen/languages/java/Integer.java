package cim4j;

/**
 * An Integer number. The range is unspecified and not limited.
 */
public class Integer extends BaseClass {

    private static final Logging LOG = Logging.getLogger(Integer.class);

    private int value = 0;

    private boolean initialized = false;

    public Integer() {
    }

    public Integer(int v) {
        value = v;
        initialized = true;
    }

    public Integer(java.lang.String s) {
        setValue(s);
    }

    @Override
    public BaseClass construct() {
        return new Integer();
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
        try {
            value = java.lang.Integer.parseInt(s.trim());
            initialized = true;
        } catch (NumberFormatException nfe) {
            LOG.error("NumberFormatException: " + nfe.getMessage());
        }
    }

    @Override
    public Object getValue() {
        return java.lang.Integer.valueOf(value);
    }

    @Override
    public void setAttribute(java.lang.String attrName, BaseClass value) {
        throw new IllegalArgumentException("Integer class cannot set attribute: " + attrName);
    }

    @Override
    public void setAttribute(java.lang.String attrName, java.lang.String value) {
        throw new IllegalArgumentException("Integer class cannot set attribute: " + attrName);
    }

    @Override
    public java.lang.String toString(boolean topClass) {
        return java.lang.Integer.toString(value);
    }

    private final java.lang.String debugName = "Integer";

    @Override
    public java.lang.String debugString() {
        return debugName;
    }
}
