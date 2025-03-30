package cim4j;

public interface BaseClassInterface {

    boolean isPrimitive();

    boolean isInitialized();

    void setValue(java.lang.String s);

    Object getValue();

    void setRdfid(java.lang.String id);

    java.lang.String getRdfid();

    java.lang.String toString(boolean topClass);

    java.lang.String debugString();

    java.lang.String getClassNamespaceUrl();
}
