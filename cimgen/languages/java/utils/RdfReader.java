package cim4j.utils;

import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.Map;
import java.util.Stack;

import javax.xml.parsers.SAXParserFactory;

import org.xml.sax.Attributes;
import org.xml.sax.SAXException;
import org.xml.sax.SAXParseException;
import org.xml.sax.helpers.DefaultHandler;

import cim4j.BaseClass;
import cim4j.CIMClassMap;
import cim4j.Logging;

/**
 * Read rdf files into a map of rdfid to cim object.
 */
public class RdfReader extends DefaultHandler {

	private static final Logging LOG = Logging.getLogger(RdfReader.class);

	private LinkedHashMap<String, BaseClass> model;
	private Stack<String> subjectStack;
	private Stack<BaseClass> objectStack;

	/**
	 * Read the cim data from a rdf file.
	 *
	 * @param path path of file to read
	 */
	public static Map<String, BaseClass> read(String path) {
		try {
			var parserFactory = SAXParserFactory.newInstance();
			parserFactory.setNamespaceAware(true);

			var parser = parserFactory.newSAXParser();
			var reader = parser.getXMLReader();

			var handler = new RdfReader();
			reader.setContentHandler(handler);
			reader.setErrorHandler(handler);

			reader.parse(path);

			return handler.getModel();
		} catch (Exception ex) {
			String txt = "Error while reading rdf file: " + path;
			LOG.error(txt, ex);
			throw new RuntimeException(txt, ex);
		}
	}

	public Map<String, BaseClass> getModel() {
		return Collections.unmodifiableMap(model);
	}

	@Override
	public void startDocument() {
		model = new LinkedHashMap<>();
		subjectStack = new Stack<>();
		objectStack = new Stack<>();
	}

	@Override
	public void characters(char[] ch, int start, int length) {
		String content = String.valueOf(ch, start, length);
		if (!content.isBlank() && !subjectStack.empty()) {
			String subject = subjectStack.peek();
			if (!objectStack.empty()) {
				BaseClass object = objectStack.peek();
				object.setAttribute(subject, content);
			} else {
				LOG.error(String.format("Cannot set attribute with name %s because object stack is empty", subject));
			}
		}
	}


	@Override
	public void startElement(String namespaceUri, String localName, String qName, Attributes attributes) {
		String rdfid = "";
		if (!qName.startsWith("cim")) {
			return;
		}

		int lastDot = localName.lastIndexOf('.');
		String attributeName;
		if (lastDot > 0) {
			attributeName = localName.substring(lastDot + 1);
		} else {
			attributeName = localName;
		}

		subjectStack.push(attributeName);
		System.out.println("Attribute is a " + attributeName);

		for (int i = 0; i < atts.getLength(); i++) {
			// System.out.println("name is " + atts.getQName(i));
			// System.out.println("value is " + atts.getValue(i));

			if (atts.getQName(i) == "rdf:ID") {
				// System.out.println("rdf:ID is " + atts.getValue(i));
				rdfid = atts.getValue(i);

				// If we have a class, make a new object and record it in the map
				if (CIMClassMap.isCIMClass(localName)) {
					cim4j.BaseClass bc = CIMClassMap.classMap.get(localName);
					if (model.containsKey(rdfid)) {
						BaseClass object = model.get(rdfid);
						System.out.println("Object: " + rdfid + " already exists and is a " + object.debugString());
						objectStack.push(object);
					} else {
						BaseClass object = bc.construct();
						System.out.println("Object: " + rdfid + " being created as a " + object.debugString());
						model.put(rdfid, object);
						objectStack.push(object);
					}
				}

				// If we have an attribute pointing to a class that exists, set
				// the reference to that instance and check for reverse pointers
			} else if (atts.getQName(i) == "rdf:resource") {
				System.out.println("rdf:resource is " + atts.getValue(i));
			}
		}

		// if we have an attribute pointing to a class that doesn't exist,
		// create the class in the map with the reverse pointer set.

	}

	@Override
	public void endElement(String namespaceUri, String localName, String qName) {
		if (!subjectStack.empty()) {
			subjectStack.pop();
		}
		if (CIMClassMap.isCIMClass(localName)) {
			if (objectStack.size() == 0) {
				System.out.println("WARNING: Nearly tried to pop empty object stack for tag: " + qName);
			} else {
				objectStack.pop();
			}
		}
	}

	@Override
	public void endDocument() {
		for (String key : model.keySet()) {
			var value = model.get(key);
			String type = value.debugString();
			LOG.debug(String.format("Model contains a %s with rdf:ID %s and attributes:", type, key));
			LOG.debug(value.toString(true));
		}
	}

	@Override
	public void warning(SAXParseException ex) {
		LOG.warn(getParseExceptionInfo(ex), ex);
	}

	@Override
	public void error(SAXParseException ex) {
		LOG.error(getParseExceptionInfo(ex), ex);
	}

	@Override
	public void fatalError(SAXParseException ex) throws SAXException {
		String txt = getParseExceptionInfo(ex);
		LOG.fatal(txt, ex);
		throw new SAXException(txt, ex);
	}

	private String getParseExceptionInfo(SAXParseException ex) {
		String systemId = ex.getSystemId();
		return "URI=" + systemId + " Line=" + ex.getLineNumber() + ": " + ex.getMessage();
	}
}
