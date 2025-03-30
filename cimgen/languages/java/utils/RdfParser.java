package cim4j.utils;

import java.io.InputStream;
import java.util.ArrayList;
import java.util.List;
import java.util.function.Consumer;

import javax.xml.namespace.QName;
import javax.xml.stream.XMLInputFactory;
import javax.xml.stream.XMLStreamConstants;
import javax.xml.stream.XMLStreamException;
import javax.xml.stream.XMLStreamReader;

import cim4j.CimConstants;

/**
 * Read RDF files into a map of rdfid to CIM object.
 */
public final class RdfParser {

    private static final String RDF = CimConstants.NAMESPACES_MAP.get("rdf");
    private static final String MD = CimConstants.NAMESPACES_MAP.get("md"); // ModelDescription

    /**
     * Parse the CIM data from a stream.
     *
     * The stream is expected to contain RDF/XML data which represent CIM data. For
     * each element with attributes the consumer createCimObjectFunction is called.
     *
     * @param stream          Input stream to parse
     * @param createCimObject Consumer function
     */
    public static void parse(InputStream stream, Consumer<Element> createCimObjectFunction) {
        try {
            var factory = XMLInputFactory.newInstance();
            var parser = factory.createXMLStreamReader(stream);

            // Check if root element has RDF namespace
            parser.nextTag();
            if (!parser.getName().getNamespaceURI().equals(RDF)) {
                throw new RuntimeException("No RDF data");
            }

            // Parse over all elements
            while (parser.hasNext()) {
                int eventType = parser.next();
                if (eventType == XMLStreamConstants.START_ELEMENT && !parser.getName().getNamespaceURI().equals(MD)) {
                    var element = new Element();
                    element.name = parser.getName();
                    element.id = getIdOrAbout(parser);

                    // Parse over the attributes of the element
                    element.attributes = parseAttributes(parser, element.name);

                    // Call the consumer function for each element
                    createCimObjectFunction.accept(element);
                }
            }
        } catch (Exception ex) {
            throw new RuntimeException("Error while parsing RDF/XML data", ex);
        }
    }

    private static List<Attribute> parseAttributes(XMLStreamReader parser, QName outerName) throws XMLStreamException {
        var attributeList = new ArrayList<Attribute>();
        var attribute = new Attribute();

        // Parse over all attributes
        while (parser.hasNext()) {
            int eventType = parser.next();

            if (eventType == XMLStreamConstants.START_ELEMENT) {
                // Start of an attribute
                attribute.name = parser.getName();
                attribute.resource = getResource(parser);

            } else if (eventType == XMLStreamConstants.CHARACTERS && !parser.isWhiteSpace()) {
                // Value of the attribute
                attribute.value = parser.getText();

            } else if (eventType == XMLStreamConstants.END_ELEMENT) {
                if (parser.getName().equals(attribute.name)) {
                    // End of the attribute
                    attributeList.add(attribute);
                    attribute = new Attribute();
                } else if (parser.getName().equals(outerName)) {
                    // End of the element
                    break;
                }
            }
        }
        return attributeList;
    }

    private static String getIdOrAbout(XMLStreamReader parser) {
        for (int idx = 0; idx < parser.getAttributeCount(); ++idx) {
            var name = parser.getAttributeName(idx);
            if (name.getNamespaceURI().equals(RDF)) {
                var value = parser.getAttributeValue(idx);
                var local = name.getLocalPart();
                if (local.equals("ID")) {
                    return value;
                }
                if (local.equals("about")) {
                    if (value.startsWith("#")) {
                        value = value.substring(1);
                    }
                    return value;
                }
            }
        }
        return null;
    }

    private static String getResource(XMLStreamReader parser) {
        for (int idx = 0; idx < parser.getAttributeCount(); ++idx) {
            var name = parser.getAttributeName(idx);
            if (name.getNamespaceURI().equals(RDF) && name.getLocalPart().equals("resource")) {
                var value = parser.getAttributeValue(idx);
                if (value.startsWith("#")) {
                    value = value.substring(1);
                }
                return value;
            }
        }
        return null;
    }

    public static class Element {
        public QName name;
        public String id;
        public List<Attribute> attributes;
    }

    public static class Attribute {
        public QName name;
        public String resource;
        public String value;
    }
}
