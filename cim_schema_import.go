package cimgen

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"sort"
	"strings"

	"golang.org/x/net/html"
)

const (
	CGMESVersion_3_0_0  = "3.0.0"
	CGMESVersion_2_4_15 = "2.4.15"
)

// enum to determine primitve types
const (
	DataTypeString   = "String"
	DataTypeInteger  = "Integer"
	DataTypeBoolean  = "Boolean"
	DataTypeFloat    = "Float"
	DataTypeDate     = "Date"
	DataTypeDateTime = "DateTime"
)

// enum for general data types
const (
	DataTypeEnum   = "Enum"
	DataTypeObject = "Object"
	DataTypeList   = "List"
)

// enum for CGMES specific data types
const (
	DataTypeActivePower               = "ActivePower"
	DataTypeActivePowerPerCurrentFlow = "ActivePowerPerCurrentFlow"
	DataTypeActivePowerPerFrequency   = "ActivePowerPerFrequency"
	DataTypeAngleDegrees              = "AngleDegrees"
	DataTypeAngleRadians              = "AngleRadians"
	DataTypeApparentPower             = "ApparentPower"
	DataTypeArea                      = "Area"
	DataTypeCapacitance               = "Capacitance"
	DataTypeConductance               = "Conductance"
	DataTypeCurrentFlow               = "CurrentFlow"
	DataTypeFrequency                 = "Frequency"
	DataTypeInductance                = "Inductance"
	DataTypeLength                    = "Length"
	DataTypeMoney                     = "Money"
	DataTypePerCent                   = "PerCent"
	DataTypePU                        = "PU"
	DataTypeReactance                 = "Reactance"
	DataTypeReactivePower             = "ReactivePower"
	DataTypeRealEnergy                = "RealEnergy"
	DataTypeResistance                = "Resistance"
	DataTypeRotationSpeed             = "RotationSpeed"
	DataTypeSeconds                   = "Seconds"
	DataTypeSusceptance               = "Susceptance"
	DataTypeTemperature               = "Temperature"
	DataTypeVoltage                   = "Voltage"
	DataTypeVoltagePerReactivePower   = "VoltagePerReactivePower"
	DataTypeVolumeFlowRate            = "VolumeFlowRate"
	DataTypeMonthDay                  = "MonthDay"
)

// CIMAttribute represents a CIM attribute with its properties.
type CIMAttribute struct {
	Id                string
	Label             string
	Namespace         string
	Comment           string
	IsList            bool
	AssociationUsed   string
	IsAssociationUsed bool
	IsFixed           bool
	InverseRole       string
	Stereotype        string
	Range             string
	DataType          string
	IsPrimitive       bool
	RDFDomain         string
	RDFType           string
	DefaultValue      string
	IsUsed            bool
	IsEnumValue       bool
	LangType          string
	IsCIMDatatype     bool
	IsClass           bool
	Origin            string
	Origins           []string
	Categories        []string
}

// CIMType represents a CIM class/type with its properties and attributes.
type CIMType struct {
	Id         string
	Label      string
	Namespace  string
	Comment    string
	Stereotype string
	RDFType    string
	SuperType  string
	SuperTypes []string
	SubClasses []string
	Origin     string
	Origins    []string
	Categories []string
	Attributes []*CIMAttribute
}

type CIMDatatype struct {
	Id         string
	Label      string
	Namespace  string
	Comment    string
	Stereotype string
	RDFType    string
	LangType   string
	Categories []string
	Origin     string
	Origins    []string
}

type CIMPrimitive struct {
	Id         string
	Label      string
	Namespace  string
	Comment    string
	Stereotype string
	RDFType    string
	LangType   string
	Origin     string
	Origins    []string
	Categories []string
}

// CIMEnum represents a CIM enumeration with its values.
type CIMEnum struct {
	Id         string
	Label      string
	Namespace  string
	Comment    string
	Stereotype string
	RDFType    string
	Origin     string
	Origins    []string
	Values     []*CIMEnumValue
}

// CIMEnumValue represents a value of a CIM enumeration.
type CIMEnumValue struct {
	Id         string
	Label      string
	Comment    string
	Stereotype string
	RDFType    string
}

// CIMOntology represents a CIM ontology with its properties.
type CIMOntology struct {
	Id          string
	Namespace   string
	VersionIRI  string
	VersionInfo string
	Keyword     string
	RDFType     string
	Name        string
	Priority    int
}

// CIMSpecification represents the entire CIM specification with types, enums, and ontologies.
type CIMSpecification struct {
	SpecificationNamespaces map[string]string
	ProfileNamespaces       map[string]string
	Ontologies              map[string]*CIMOntology
	Types                   map[string]*CIMType
	Enums                   map[string]*CIMEnum
	PrimitiveTypes          map[string]*CIMPrimitive
	CIMDatatypes            map[string]*CIMDatatype
	CGMESVersion            string
}

// NewCIMSpecification creates and returns a new CIMSpecification instance.
func NewCIMSpecification() *CIMSpecification {
	return &CIMSpecification{
		Types:                   make(map[string]*CIMType, 0),
		Enums:                   make(map[string]*CIMEnum, 0),
		Ontologies:              make(map[string]*CIMOntology, 0),
		SpecificationNamespaces: make(map[string]string, 0),
		ProfileNamespaces:       make(map[string]string),
		PrimitiveTypes:          make(map[string]*CIMPrimitive, 0),
		CIMDatatypes:            make(map[string]*CIMDatatype, 0),
		CGMESVersion:            CGMESVersion_3_0_0,
	}
}

// ImportCIMSchemaFiles imports CIM schema files matching the given glob pattern into the CIMSpecification.
func (cimSpec *CIMSpecification) ImportCIMSchemaFiles(schemaFiles string) {
	entries, err := filepath.Glob(schemaFiles)
	if err != nil {
		panic(err)
	}
	sort.Strings(entries)

	for _, entry := range entries {
		b, err := os.ReadFile(entry)
		if err != nil {
			panic(err)
		}

		resultMap, err := DecodeToMap(bytes.NewReader(b))
		if err != nil {
			panic(err)
		}

		cimSpec.addRDFMap(resultMap)
	}

	cimSpec.postprocess()
}

// addRDFMap adds the CIM types, enums, and ontology from the input map to the CIMSpecification.
func (cimSpec *CIMSpecification) addRDFMap(inputMap map[string]interface{}) {
	cimTypes, cimEnums, cimOntology, namespaces, cimDatatypes, cimPrimitives := processRDFMap(inputMap)
	cimSpec.Types = mergeCimTypes(cimSpec.Types, cimTypes)
	cimSpec.Enums = mergeCimEnums(cimSpec.Enums, cimEnums)
	cimSpec.CIMDatatypes = mergeCIMDatatypes(cimSpec.CIMDatatypes, cimDatatypes)
	cimSpec.PrimitiveTypes = mergePrimitives(cimSpec.PrimitiveTypes, cimPrimitives)
	cimSpec.Ontologies[cimOntology.Keyword] = &cimOntology
	cimSpec.SpecificationNamespaces = mergeNamespaces(cimSpec.SpecificationNamespaces, namespaces)
}

// printSpecification prints the CIMSpecification to the provided writer in JSON format.
func (cimSpec *CIMSpecification) printSpecification(w io.Writer) {
	jsonb, err := json.MarshalIndent(cimSpec.SpecificationNamespaces, "", "  ")
	if err != nil {
		panic(err)
	}
	w.Write(jsonb)
	fmt.Fprint(w, "\n")

	jsonb, err = json.MarshalIndent(cimSpec.Ontologies, "", "  ")
	if err != nil {
		panic(err)
	}
	w.Write(jsonb)
	fmt.Fprint(w, "\n")

	jsonb, err = json.MarshalIndent(cimSpec.Types, "", "  ")
	if err != nil {
		panic(err)
	}
	w.Write(jsonb)
	fmt.Fprint(w, "\n")

	jsonb, err = json.MarshalIndent(cimSpec.Enums, "", "  ")
	if err != nil {
		panic(err)
	}
	w.Write(jsonb)
	fmt.Fprint(w, "\n")
}

// processRDFMap processes the RDF map and extracts CIM types, enums, and ontology.
func processRDFMap(inputMap map[string]interface{}) (map[string]*CIMType, map[string]*CIMEnum, CIMOntology, map[string]string, map[string]*CIMDatatype, map[string]*CIMPrimitive) {
	rdfMap := inputMap["rdf:RDF"].(map[string]interface{})
	namespaces := processNamespaces(rdfMap)

	descriptions := rdfMap["rdf:Description"].([]map[string]interface{})
	cimTypes := make(map[string]*CIMType, 0)
	cimDatatypes := make(map[string]*CIMDatatype, 0)
	cimPrimitives := make(map[string]*CIMPrimitive, 0)
	cimEnums := make(map[string]*CIMEnum, 0)
	cimEnumValues := make([]*CIMEnumValue, 0)
	cimAttributes := make([]*CIMAttribute, 0)
	var cimOntology CIMOntology

	for _, v := range descriptions {
		objType := extractResource(v, "rdf:type")

		if strings.Contains(objType, "http://www.w3.org/2000/01/rdf-schema#Class") {
			if extractStringOrResource(v["cims:stereotype"]) == "http://iec.ch/TC57/NonStandard/UML#enumeration" {
				e := processEnum(v)
				e.Origin = cimOntology.Keyword
				e.Origins = []string{cimOntology.Keyword}
				cimEnums[e.Id] = &e
			} else if extractStringOrResource(v["cims:stereotype"]) == "CIMDatatype" {
				e := processCIMDatatypes(v)
				e.Origin = cimOntology.Keyword
				e.Origins = []string{cimOntology.Keyword}
				cimDatatypes[e.Id] = &e
			} else if extractStringOrResource(v["cims:stereotype"]) == "Primitive" {
				e := processPrimitives(v)
				e.Origin = cimOntology.Keyword
				e.Origins = []string{cimOntology.Keyword}
				cimPrimitives[e.Id] = &e
			} else {
				e := processClass(v)
				e.Origin = cimOntology.Keyword
				e.Origins = []string{cimOntology.Keyword}
				cimTypes[e.Id] = &e
			}
		} else if strings.Contains(objType, "http://www.w3.org/1999/02/22-rdf-syntax-ns#Property") {
			cimAttribute := processProperty(v)
			cimAttribute.Origin = cimOntology.Keyword
			cimAttribute.Origins = []string{cimOntology.Keyword}
			cimAttributes = append(cimAttributes, &cimAttribute)
		} else if strings.Contains(objType, "http://iec.ch/TC57/1999/rdf-schema-extensions-19990926#ClassCategory") {

		} else if strings.Contains(objType, "http://www.w3.org/2002/07/owl#Ontology") {
			cimOntology = processOntology(v)
		} else {
			cimEnumValue := processEnumValue(v)
			cimEnumValues = append(cimEnumValues, &cimEnumValue)
		}
	}

	assignAttributesToTypes(cimTypes, cimAttributes)

	assignEnumValuesToEnums(cimEnums, cimEnumValues)

	return cimTypes, cimEnums, cimOntology, namespaces, cimDatatypes, cimPrimitives
}

// processNamespaces collects all namespaces declared in the specification
func processNamespaces(rdfMap map[string]interface{}) map[string]string {
	namespaces := make(map[string]string)
	// iterate over rdfMap and process each element that is @xml or @xmlns
	for k, v := range rdfMap {
		if strings.HasPrefix(k, "@xmlns:") {
			// add # at the end of the namespace URI if not present
			ns := v.(string)
			if !strings.HasSuffix(ns, "#") {
				ns += "#"
			}
			namespaces[strings.TrimPrefix(k, "@xmlns:")] = ns
		}
		if strings.HasPrefix(k, "@xml:") {
			// add # at the end of the namespace URI if not present
			ns := v.(string)
			if !strings.HasSuffix(ns, "#") {
				ns += "#"
			}
			namespaces[strings.TrimPrefix(k, "@xml:")] = ns
		}
	}
	return namespaces
}

// processClass processes a map representing a CIM class and returns a CIMType struct.
func processClass(classMap map[string]interface{}) CIMType {

	id := extractValue(classMap, "@rdf:about")
	label := extractText(classMap, "rdfs:label")
	superType := extractResource(classMap, "rdfs:subClassOf")
	comment := extractText(classMap, "rdfs:comment")
	stereotype := extractStringOrResource(classMap["cims:stereotype"])
	category := extractResource(classMap, "cims:belongsToCategory")
	rdfType := extractResource(classMap, "rdf:type")
	namespace := extractURIPath(id)
	comment = cleanText(comment)

	return CIMType{
		Id:         extractURIEnd(id),
		Label:      label,
		SuperType:  extractURIEnd(superType),
		Comment:    comment,
		Namespace:  namespace,
		Stereotype: extractURIEnd(stereotype),
		RDFType:    extractURIEnd(rdfType),
		Categories: []string{extractURIEnd(category)},
		Attributes: make([]*CIMAttribute, 0),
	}
}

// processPrimitives processes a map representing a CIM class and returns a CIMPrimitive struct.
func processPrimitives(classMap map[string]interface{}) CIMPrimitive {

	id := extractValue(classMap, "@rdf:about")
	label := extractText(classMap, "rdfs:label")
	comment := extractText(classMap, "rdfs:comment")
	stereotype := extractStringOrResource(classMap["cims:stereotype"])
	category := extractResource(classMap, "cims:belongsToCategory")
	rdfType := extractResource(classMap, "rdf:type")
	namespace := extractURIPath(id)
	comment = cleanText(comment)

	return CIMPrimitive{
		Id:         extractURIEnd(id),
		Label:      label,
		Comment:    comment,
		Namespace:  namespace,
		Stereotype: extractURIEnd(stereotype),
		RDFType:    extractURIEnd(rdfType),
		Categories: []string{extractURIEnd(category)},
	}
}

// processCIMDatatypes processes a map representing a CIM class and returns a CIMDatatypes struct.
func processCIMDatatypes(classMap map[string]interface{}) CIMDatatype {

	typeId := extractValue(classMap, "@rdf:about")
	label := extractText(classMap, "rdfs:label")
	comment := extractText(classMap, "rdfs:comment")
	stereotype := extractStringOrResource(classMap["cims:stereotype"])
	category := extractResource(classMap, "cims:belongsToCategory")
	rdfType := extractResource(classMap, "rdf:type")
	namespace := extractURIPath(typeId)
	comment = cleanText(comment)

	return CIMDatatype{
		Id:         extractURIEnd(typeId),
		Label:      label,
		Comment:    comment,
		Namespace:  namespace,
		Stereotype: extractURIEnd(stereotype),
		RDFType:    extractURIEnd(rdfType),
		Categories: []string{extractURIEnd(category)},
	}
}

// processProperty processes a map representing a CIM property and returns a CIMAttribute struct.
func processProperty(classMap map[string]interface{}) CIMAttribute {
	attrId := extractValue(classMap, "@rdf:about")
	rdfType := extractResource(classMap, "rdf:type")
	comment := extractText(classMap, "rdfs:comment")
	stereotype := extractStringOrResource(classMap["cims:stereotype"])
	label := extractText(classMap, "rdfs:label")
	rdfDomain := extractResource(classMap, "rdfs:domain")
	cimDataType := extractResource(classMap, "cims:dataType")
	rdfRange := extractResource(classMap, "rdfs:range")
	inverseRoleName := extractResource(classMap, "cims:inverseRoleName")
	comment = cleanText(comment)
	namespace := extractURIPath(attrId)

	associationUsed := strings.ToLower(extractStringOrResource(classMap["cims:AssociationUsed"]))

	isList := false
	multiplicity := extractResource(classMap, "cims:multiplicity")
	if multiplicity == "http://iec.ch/TC57/1999/rdf-schema-extensions-19990926#M:0..n" || multiplicity == "http://iec.ch/TC57/1999/rdf-schema-extensions-19990926#M:1..n" {
		isList = true
	}

	return CIMAttribute{
		Id:              extractURIEnd(attrId),
		Comment:         comment,
		Stereotype:      extractURIEnd(stereotype),
		Namespace:       namespace,
		Label:           label,
		RDFDomain:       extractURIEnd(rdfDomain),
		DataType:        extractURIEnd(cimDataType),
		Range:           extractURIEnd(rdfRange),
		RDFType:         extractURIEnd(rdfType),
		AssociationUsed: associationUsed,
		InverseRole:     extractURIEnd(inverseRoleName),
		IsList:          isList,
	}
}

func cleanText(htmlString string) string {
	plainText, err := stripTagsManual(htmlString)
	if err != nil {
		fmt.Printf("Error: %v\n", err)
		return ""
	}

	// Replace ’ with `
	plainText = strings.ReplaceAll(plainText, "’", "'")
	// Replace ' with `
	plainText = strings.ReplaceAll(plainText, "'", "'")
	// Replace “ with `
	plainText = strings.ReplaceAll(plainText, "“", "'")
	// Replace ” with `
	plainText = strings.ReplaceAll(plainText, "”", "'")
	// Replace " with `
	plainText = strings.ReplaceAll(plainText, "\"", "'")
	// Replace – with -
	plainText = strings.ReplaceAll(plainText, "–", "-")

	// Remove line breaks and extra spaces
	plainText = strings.ReplaceAll(plainText, "\n", " ")
	plainText = strings.ReplaceAll(plainText, "\r", " ")
	plainText = strings.Join(strings.Fields(plainText), " ")

	// Clean up leading/trailing whitespace and normalize spacing
	return strings.TrimSpace(plainText)
}

// stripTagsManual parses HTML from a string and extracts only the plain text content.
func stripTagsManual(htmlInput string) (string, error) {
	// Use strings.NewReader to create an io.Reader from the input string
	doc, err := html.Parse(strings.NewReader(htmlInput))
	if err != nil {
		return "", fmt.Errorf("failed to parse HTML: %w", err)
	}

	var builder strings.Builder
	// Call the recursive function to traverse the nodes and extract text
	traverseAndExtractText(doc, &builder)

	return builder.String(), nil
}

// traverseAndExtractText recursively walks the HTML node tree and appends text nodes to a strings.Builder.
func traverseAndExtractText(n *html.Node, builder *strings.Builder) {
	// If the node is a TextNode, append its data to the builder
	if n.Type == html.TextNode {
		builder.WriteString(n.Data)
	}

	// Recurse through all child nodes
	for c := n.FirstChild; c != nil; c = c.NextSibling {
		traverseAndExtractText(c, builder)
	}
}

// processEnum processes a map representing a CIM enumeration and returns a CIMEnum struct.
func processEnum(classMap map[string]interface{}) CIMEnum {

	id := extractValue(classMap, "@rdf:about")
	label := extractText(classMap, "rdfs:label")
	comment := extractText(classMap, "rdfs:comment")
	stereotype := extractStringOrResource(classMap["cims:stereotype"])
	rdfType := extractResource(classMap, "rdf:type")
	namespace := extractURIPath(id)

	return CIMEnum{
		Id:         extractURIEnd(id),
		Label:      label,
		Comment:    comment,
		Namespace:  namespace,
		Stereotype: extractURIEnd(stereotype),
		RDFType:    extractURIEnd(rdfType),
	}
}

// processEnumValue processes a map representing a CIM enumeration value and returns a CIMEnumValue struct.
func processEnumValue(classMap map[string]interface{}) CIMEnumValue {

	id := extractValue(classMap, "@rdf:about")
	label := extractText(classMap, "rdfs:label")
	comment := extractText(classMap, "rdfs:comment")
	stereotype := extractStringOrResource(classMap["cims:stereotype"])
	rdfType := extractResource(classMap, "rdf:type")

	return CIMEnumValue{
		Id:         extractURIEnd(id),
		Label:      label,
		Comment:    comment,
		Stereotype: extractURIEnd(stereotype),
		RDFType:    extractURIEnd(rdfType),
	}
}

// processOntology processes a map representing a CIM ontology and returns a CIMOntology struct.
func processOntology(classMap map[string]interface{}) CIMOntology {

	id := extractValue(classMap, "@rdf:about")
	rdfType := extractResource(classMap, "rdf:type")
	versionIRI := extractResource(classMap, "owl:versionIRI")
	versionInfo := extractText(classMap, "owl:versionInfo")
	keyword := extractValue(classMap, "dcat:keyword")
	name := extractText(classMap, "dct:title")
	// remove suffix " Vocabulary" from name if present
	name = strings.TrimSuffix(name, " Vocabulary")

	return CIMOntology{
		Id:          extractURIEnd(id),
		Namespace:   extractURIPath(id),
		RDFType:     extractURIEnd(rdfType),
		VersionIRI:  versionIRI,
		VersionInfo: versionInfo,
		Keyword:     keyword,
		Name:        name,
	}
}

// assignAttributesToTypes assigns attributes to their corresponding CIM types based on RDFDomain.
func assignAttributesToTypes(cimTypes map[string]*CIMType, cimAttributes []*CIMAttribute) {
	for _, attr := range cimAttributes {
		if v, ok := cimTypes[attr.RDFDomain]; ok {
			attr.Categories = v.Categories
			v.Attributes = append(v.Attributes, attr)
		}
	}
}

// assignEnumValuesToEnums assigns enum values to their corresponding CIM enums based on RDFType.
func assignEnumValuesToEnums(cimEnums map[string]*CIMEnum, cimEnumValues []*CIMEnumValue) {
	for _, val := range cimEnumValues {
		if enum, ok := cimEnums[val.RDFType]; ok {
			enum.Values = append(enum.Values, val)
		}
	}
}

// mergeNamepaces merges two maps of namespaces.
func mergeNamespaces(namespacesMerged map[string]string, namespaces map[string]string) map[string]string {
	for k, v := range namespaces {
		if _, ok := namespacesMerged[k]; !ok {
			namespacesMerged[k] = v
		}
	}
	return namespacesMerged
}

// mergeCimTypes merges two maps of CIM types, combining attributes and origins for types with the same Id.
func mergeCimTypes(typesMerged map[string]*CIMType, types map[string]*CIMType) map[string]*CIMType {
	for k := range types {
		if v, ok := typesMerged[k]; ok {
			if types[k].SuperType != "" {
				v.SuperType = types[k].SuperType
			}

			if types[k].Stereotype != "" {
				v.Stereotype = types[k].Stereotype
			}

			if len(types[k].Categories) > 0 {
				v.Categories = append(v.Categories, types[k].Categories...)
			}

			if types[k].Origin != "" {
				v.Origins = append(v.Origins, types[k].Origin)
			}

			for _, attr := range types[k].Attributes {
				if existingAttrIndex := FindCIMAttributeById(v.Attributes, attr.Id); existingAttrIndex != -1 {
					// If the attribute already exists, we can merge the attributes
					existingAttr := v.Attributes[existingAttrIndex]
					existingAttr.Origins = append(existingAttr.Origins, attr.Origin)
					existingAttr.Categories = append(existingAttr.Categories, attr.Categories...)
				} else {
					v.Attributes = append(v.Attributes, attr)
				}
			}
		} else {
			typesMerged[k] = types[k]
		}
	}
	return typesMerged
}

// FindCIMAttributeById searches for a CIMAttribute with the given Id in a slice.
func FindCIMAttributeById(attrs []*CIMAttribute, id string) int {
	for i, attr := range attrs {
		if attr.Id == id {
			return i
		}
	}
	return -1
}

// mergeCimEnums merges two maps of CIM enums, combining values and origins for enums with the same Id.
func mergeCimEnums(enumsMerged map[string]*CIMEnum, enums map[string]*CIMEnum) map[string]*CIMEnum {
	for k := range enums {
		if v, ok := enumsMerged[k]; ok {
			if enums[k].Stereotype != "" {
				v.Stereotype = enums[k].Stereotype
			}

			if enums[k].Origin != "" {
				v.Origins = append(v.Origins, enums[k].Origin)
			}

			for _, val := range enums[k].Values {
				if existingValIndex := FindCIMEnumValueById(v.Values, val.Id); existingValIndex == -1 {
					v.Values = append(v.Values, val)
				}
			}
		} else {
			enumsMerged[k] = enums[k]
		}
	}
	return enumsMerged
}

// FindCIMEnumValueById searches for a CIMEnumValue with the given Id in a slice.
func FindCIMEnumValueById(vals []*CIMEnumValue, id string) int {
	for i, val := range vals {
		if val.Id == id {
			return i
		}
	}
	return -1
}

func mergeCIMDatatypes(typesMerged map[string]*CIMDatatype, types map[string]*CIMDatatype) map[string]*CIMDatatype {
	for k := range types {
		if v, ok := typesMerged[k]; ok {
			if types[k].Stereotype != "" {
				v.Stereotype = types[k].Stereotype
			}

			if types[k].Origin != "" {
				v.Origins = append(v.Origins, types[k].Origin)
			}
		} else {
			typesMerged[k] = types[k]
		}
	}
	return typesMerged
}

func mergePrimitives(typesMerged map[string]*CIMPrimitive, types map[string]*CIMPrimitive) map[string]*CIMPrimitive {
	for k := range types {
		if v, ok := typesMerged[k]; ok {
			if types[k].Stereotype != "" {
				v.Stereotype = types[k].Stereotype
			}

			if types[k].Origin != "" {
				v.Origins = append(v.Origins, types[k].Origin)
			}
		} else {
			typesMerged[k] = types[k]
		}
	}
	return typesMerged
}

// extractResource extracts the resource URI from a map object using the specified key.
// It returns an empty string if the key does not exist or the value is not a map.
func extractResource(obj map[string]interface{}, key string) string {
	if v, ok := obj[key]; ok {
		if m, ok := v.(map[string]interface{}); ok {
			return m["@rdf:resource"].(string)
		}
	}
	return ""
}

// extractStringOrResource extracts a string value or a resource URI from an interface{}.
// It handles cases where the input is a string, a map with a resource, or a slice of maps.
// It returns an empty string if no valid value is found.
func extractStringOrResource(obj interface{}) string {
	switch item := obj.(type) {
	case string:
		return item
	case map[string]interface{}:
		return item["@rdf:resource"].(string)
	case []interface{}:
		for _, m := range item {
			if m, ok := m.(map[string]interface{}); ok {
				return m["@rdf:resource"].(string)
			}
		}
	}
	return ""
}

// extractText extracts the text value from a map object using the specified key.
// It returns an empty string if the key does not exist or the value is not a map.
func extractText(obj map[string]interface{}, key string) string {
	if v, ok := obj[key]; ok {
		if m, ok := v.(map[string]interface{}); ok {
			return m["_"].(string)
		}
	}
	return ""
}

// extractValue extracts a string value from a map object using the specified key.
// It returns an empty string if the key does not exist.
func extractValue(obj map[string]interface{}, key string) string {
	if t, ok := obj[key]; ok {
		return t.(string)
	}
	return ""
}

// extractURIEnd extracts the fragment identifier from a URI (the part after the '#').
func extractURIEnd(uri string) string {
	l := strings.Split(uri, "#")
	return l[len(l)-1]
}

// extractURIPath extracts the path part of a URI (the part before the '#').
func extractURIPath(uri string) string {
	l := strings.Split(uri, "#")
	return l[0]
}
