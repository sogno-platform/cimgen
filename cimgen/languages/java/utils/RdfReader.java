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

	private BaseClass createOrLinkObject(String className, String rdfid) {
		if (rdfid.startsWith("#")) {
			rdfid = rdfid.substring(1);
		}
		final BaseClass template = CIMClassMap.classMap.get(className);
		if (template != null) {
			BaseClass object;
			if (model.containsKey(rdfid)) {
				object = model.get(rdfid);
				var oldType = object.getClass();
				var newType = template.getClass();
				if (!oldType.equals(newType) && oldType.isAssignableFrom(newType)) {
					var oldObject = object;
					LOG.debug(String.format("Retyping object with rdf:ID: %s from type: %s to type: %s", rdfid,
							oldObject.debugString(), className));
					// Create new object with new type
					object = template.construct();
					object.setRdfid(rdfid);
					// Copy attributes from old object to the new object
					for (String attrName : oldObject.getAttributeNames()) {
						var attrObj = oldObject.getAttribute(attrName);
						if (attrObj != null) {
							object.setAttribute(attrName, attrObj);
						}
					}
					// Replace old object with new object in attributes of all objects in the model
					for (var cimObj : model.values()) {
						for (String attrName : cimObj.getAttributeNames()) {
							if (cimObj.getAttribute(attrName) == oldObject) {
								cimObj.setAttribute(attrName, object);
							}
						}
					}
					// Replace old object with new object in model
					model.put(rdfid, object);
				} else {
					LOG.debug(String.format("Found %s with rdf:ID: %s in map", object.debugString(), rdfid));
				}
			} else {
				LOG.debug(String.format("Creating object of type: %s with rdf:ID: %s", className, rdfid));
				object = template.construct();
				object.setRdfid(rdfid);
				model.put(rdfid, object);
			}
			return object;
		}

		LOG.debug(String.format("Could not find %s in map", className));
		return null;
	}

	@Override
	public void startElement(String namespaceUri, String localName, String qName, Attributes attributes) {
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

		for (int idx = 0; idx < attributes.getLength(); ++idx) {
			qName = attributes.getQName(idx);
			if (qName.equals("rdf:ID") || qName.equals("rdf:about")) {
				String rdfid = attributes.getValue(idx);

				// If we have a class, make a new object and record it in the map
				if (CIMClassMap.isCIMClass(localName)) {
					BaseClass object = createOrLinkObject(localName, rdfid);
					objectStack.push(object);
				} else {
					LOG.debug(String.format("Possible class element: %s", qName));
				}
			}
			if (qName.equals("rdf:resource")) {
				String rdfid = attributes.getValue(idx);

				if (!objectStack.isEmpty()) {
					BaseClass object = objectStack.peek();
					if (object != null) {
						BaseClass attributeObject = createOrLinkObject("IdentifiedObject", rdfid);
						object.setAttribute(attributeName, attributeObject);
					}
				}
			}
		}
	}

	@Override
	public void endElement(String namespaceUri, String localName, String qName) {
		if (!subjectStack.empty()) {
			subjectStack.pop();
		}
		if (CIMClassMap.isCIMClass(localName)) {
			if (!objectStack.empty()) {
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
