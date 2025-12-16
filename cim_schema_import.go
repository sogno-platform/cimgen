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
	DateTypeDecimal  = "Decimal"
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
	Id                   string   // from RDF schema
	Label                string   // from RDF schema
	Namespace            string   // from RDF schema
	Comment              string   // from RDF schema
	CIMMultiplicity      string   // from RDF schema
	IsList               bool     // derived
	CIMAssociationUsed   string   // from RDF schema
	IsAssociationUsed    bool     // derived
	IsFixed              bool     // TODO from RDF schema
	CIMInverseRole       string   // from RDF schema
	HasInverseRole       bool     // derived
	InverseRoleAttribute string   // derived
	CIMStereotype        string   // from RDF schema
	RDFRange             string   // from RDF schema
	CIMDataType          string   // from RDF schema
	DataType             string   // derived
	IsPrimitive          bool     // derived
	RDFDomain            string   // from RDF schema
	RDFType              string   // from RDF schema
	DefaultValue         string   // derived
	IsUsed               bool     // derived
	IsEnumValue          bool     // derived
	LangType             string   // derived
	IsCIMDatatype        bool     // derived
	IsClass              bool     // derived
	Origin               string   // derived
	Origins              []string // from RDF schema
	CIMCategories        []string // from RDF schema
}

// CIMType represents a CIM class/type with its properties and attributes.
type CIMType struct {
	Id            string          // from RDF schema
	Label         string          // from RDF schema
	Namespace     string          // from RDF schema
	Comment       string          // from RDF schema
	CIMStereotype string          // from RDF schema
	RDFType       string          // from RDF schema
	SuperType     string          // from RDF schema
	SuperTypes    []string        // TODO derived
	SubTypes      []string        // TODO derived
	Origin        string          // derived
	Origins       []string        // from RDF schema
	CIMCategories []string        // from RDF schema
	Attributes    []*CIMAttribute // from RDF schema
}

type CIMDatatype struct {
	Id            string          // from RDF schema
	Label         string          // from RDF schema
	Namespace     string          // from RDF schema
	Comment       string          // from RDF schema
	CIMStereotype string          // from RDF schema
	RDFType       string          // from RDF schema
	LangType      string          // derived
	PrimitiveType string          // derived
	CIMCategory   string          // from RDF schema
	Attributes    []*CIMAttribute // from RDF schema
}

type CIMPrimitive struct {
	Id            string // from RDF schema
	Label         string // from RDF schema
	Namespace     string // from RDF schema
	Comment       string // from RDF schema
	CIMStereotype string // from RDF schema
	RDFType       string // from RDF schema
	LangType      string // derived
}

// CIMEnum represents a CIM enumeration with its values.
type CIMEnum struct {
	Id            string          // from RDF schema
	Label         string          // from RDF schema
	Namespace     string          // from RDF schema
	Comment       string          // from RDF schema
	CIMStereotype string          // from RDF schema
	RDFType       string          // from RDF schema
	Origin        string          // derived
	Origins       []string        // from RDF schema
	Values        []*CIMEnumValue // from RDF schema
}

// CIMEnumValue represents a value of a CIM enumeration.
type CIMEnumValue struct {
	Id            string // from RDF schema
	Label         string // from RDF schema
	Comment       string // from RDF schema
	CIMStereotype string // from RDF schema
	RDFType       string // from RDF schema
}

// CIMOntology represents a CIM ontology with its properties.
type CIMOntology struct {
	Id             string // from RDF schema
	Namespace      string // from RDF schema
	OWLVersionIRI  string // from RDF schema
	OWLVersionInfo string // from RDF schema
	Keyword        string // from RDF schema
	RDFType        string // from RDF schema
	Name           string // from RDF schema
	Priority       int    // derived
}

// CIMSpecification represents the entire CIM specification with types, enums, and ontologies.
type CIMSpecification struct {
	SpecificationNamespaces map[string]string
	ProfileNamespaces       map[string]string
	Ontologies              map[string]*CIMOntology
	OntologyList            []*CIMOntology
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
		OntologyList:            make([]*CIMOntology, 0),
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
	fmt.Fprint(w, "[\n")
	jsonb, err := json.MarshalIndent(cimSpec.SpecificationNamespaces, "", "  ")
	if err != nil {
		panic(err)
	}
	w.Write(jsonb)
	fmt.Fprint(w, ",\n")

	jsonb, err = json.MarshalIndent(cimSpec.Ontologies, "", "  ")
	if err != nil {
		panic(err)
	}
	w.Write(jsonb)
	fmt.Fprint(w, ",\n")

	jsonb, err = json.MarshalIndent(cimSpec.Types, "", "  ")
	if err != nil {
		panic(err)
	}
	w.Write(jsonb)
	fmt.Fprint(w, ",\n")

	jsonb, err = json.MarshalIndent(cimSpec.Enums, "", "  ")
	if err != nil {
		panic(err)
	}
	w.Write(jsonb)
	fmt.Fprint(w, ",\n")

	jsonb, err = json.MarshalIndent(cimSpec.CIMDatatypes, "", "  ")
	if err != nil {
		panic(err)
	}
	w.Write(jsonb)
	fmt.Fprint(w, ",\n")

	jsonb, err = json.MarshalIndent(cimSpec.PrimitiveTypes, "", "  ")
	if err != nil {
		panic(err)
	}
	w.Write(jsonb)
	fmt.Fprint(w, "\n]\n")
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
				cimDatatypes[e.Id] = &e
			} else if extractStringOrResource(v["cims:stereotype"]) == "Primitive" {
				e := processPrimitives(v)
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
	assignAttributesToCIMDataTypes(cimDatatypes, cimAttributes)

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
	return CIMType{
		Id:            extractURIEnd(extractValue(classMap, "@rdf:about")),
		Label:         extractText(classMap, "rdfs:label"),
		SuperType:     extractURIEnd(extractResource(classMap, "rdfs:subClassOf")),
		Comment:       cleanText(extractText(classMap, "rdfs:comment")),
		Namespace:     extractURIPath(extractValue(classMap, "@rdf:about")),
		CIMStereotype: extractURIEnd(extractStringOrResource(classMap["cims:stereotype"])),
		RDFType:       extractURIEnd(extractResource(classMap, "rdf:type")),
		CIMCategories: []string{extractURIEnd(extractResource(classMap, "cims:belongsToCategory"))},
		Attributes:    make([]*CIMAttribute, 0),
	}
}

// processPrimitives processes a map representing a CIM class and returns a CIMPrimitive struct.
func processPrimitives(classMap map[string]interface{}) CIMPrimitive {
	return CIMPrimitive{
		Id:            extractURIEnd(extractValue(classMap, "@rdf:about")),
		Label:         extractText(classMap, "rdfs:label"),
		Comment:       cleanText(extractText(classMap, "rdfs:comment")),
		Namespace:     extractURIPath(extractValue(classMap, "@rdf:about")),
		CIMStereotype: extractURIEnd(extractStringOrResource(classMap["cims:stereotype"])),
		RDFType:       extractURIEnd(extractResource(classMap, "rdf:type")),
	}
}

// processCIMDatatypes processes a map representing a CIM class and returns a CIMDatatypes struct.
func processCIMDatatypes(classMap map[string]interface{}) CIMDatatype {
	return CIMDatatype{
		Id:            extractURIEnd(extractValue(classMap, "@rdf:about")),
		Label:         extractText(classMap, "rdfs:label"),
		Comment:       cleanText(extractText(classMap, "rdfs:comment")),
		Namespace:     extractURIPath(extractValue(classMap, "@rdf:about")),
		CIMStereotype: extractURIEnd(extractStringOrResource(classMap["cims:stereotype"])),
		RDFType:       extractURIEnd(extractResource(classMap, "rdf:type")),
		CIMCategory:   extractURIEnd(extractResource(classMap, "cims:belongsToCategory")),
	}
}

// processProperty processes a map representing a CIM property and returns a CIMAttribute struct.
func processProperty(classMap map[string]interface{}) CIMAttribute {
	associationUsed := strings.ToLower(extractStringOrResource(classMap["cims:AssociationUsed"]))
	return CIMAttribute{
		Id:                 extractURIEnd(extractValue(classMap, "@rdf:about")),
		Namespace:          extractURIPath(extractValue(classMap, "@rdf:about")),
		Label:              extractText(classMap, "rdfs:label"),
		Comment:            cleanText(extractText(classMap, "rdfs:comment")),
		CIMStereotype:      extractURIEnd(extractStringOrResource(classMap["cims:stereotype"])),
		RDFDomain:          extractURIEnd(extractResource(classMap, "rdfs:domain")),
		CIMDataType:        extractURIEnd(extractResource(classMap, "cims:dataType")),
		RDFRange:           extractURIEnd(extractResource(classMap, "rdfs:range")),
		RDFType:            extractURIEnd(extractResource(classMap, "rdf:type")),
		CIMAssociationUsed: associationUsed,
		IsAssociationUsed:  isAssociationUsed(associationUsed),
		CIMInverseRole:     extractURIEnd(extractResource(classMap, "cims:inverseRoleName")),
		CIMMultiplicity:    extractResource(classMap, "cims:multiplicity"),
		IsList:             isListAttribute(extractResource(classMap, "cims:multiplicity")),
	}
}

func isListAttribute(multiplicity string) bool {
	return multiplicity == "http://iec.ch/TC57/1999/rdf-schema-extensions-19990926#M:0..n" || multiplicity == "http://iec.ch/TC57/1999/rdf-schema-extensions-19990926#M:1..n"
}

func isAssociationUsed(associationUsed string) bool {
	return associationUsed == "yes" || associationUsed == ""
}

func cleanText(htmlString string) string {
	plainText, err := stripTagsManual(htmlString)
	if err != nil {
		fmt.Printf("Error: %v\n", err)
		return ""
	}

	plainText = strings.ReplaceAll(plainText, "’", "'")
	plainText = strings.ReplaceAll(plainText, "'", "'")
	plainText = strings.ReplaceAll(plainText, "“", "'")
	plainText = strings.ReplaceAll(plainText, "”", "'")
	plainText = strings.ReplaceAll(plainText, "\"", "'")
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
	return CIMEnum{
		Id:            extractURIEnd(extractValue(classMap, "@rdf:about")),
		Label:         extractText(classMap, "rdfs:label"),
		Comment:       extractText(classMap, "rdfs:comment"),
		Namespace:     extractURIPath(extractValue(classMap, "@rdf:about")),
		CIMStereotype: extractURIEnd(extractStringOrResource(classMap["cims:stereotype"])),
		RDFType:       extractURIEnd(extractResource(classMap, "rdf:type")),
	}
}

// processEnumValue processes a map representing a CIM enumeration value and returns a CIMEnumValue struct.
func processEnumValue(classMap map[string]interface{}) CIMEnumValue {
	return CIMEnumValue{
		Id:            extractURIEnd(extractValue(classMap, "@rdf:about")),
		Label:         extractText(classMap, "rdfs:label"),
		Comment:       extractText(classMap, "rdfs:comment"),
		CIMStereotype: extractURIEnd(extractStringOrResource(classMap["cims:stereotype"])),
		RDFType:       extractURIEnd(extractResource(classMap, "rdf:type")),
	}
}

// processOntology processes a map representing a CIM ontology and returns a CIMOntology struct.
func processOntology(classMap map[string]interface{}) CIMOntology {
	return CIMOntology{
		Id:             extractURIEnd(extractValue(classMap, "@rdf:about")),
		Namespace:      extractURIPath(extractValue(classMap, "@rdf:about")),
		RDFType:        extractURIEnd(extractResource(classMap, "rdf:type")),
		OWLVersionIRI:  extractResource(classMap, "owl:versionIRI"),
		OWLVersionInfo: extractText(classMap, "owl:versionInfo"),
		Keyword:        extractValue(classMap, "dcat:keyword"),
		// remove suffix " Vocabulary" from name if present
		Name: strings.TrimSuffix(extractText(classMap, "dcterms:title"), " Vocabulary"),
	}
}

// assignAttributesToTypes assigns attributes to their corresponding CIM types based on RDFDomain.
func assignAttributesToTypes(cimTypes map[string]*CIMType, attributes []*CIMAttribute) {
	for _, attr := range attributes {
		if v, ok := cimTypes[attr.RDFDomain]; ok {
			attr.CIMCategories = v.CIMCategories
			v.Attributes = append(v.Attributes, attr)
		}
	}
}

func assignAttributesToCIMDataTypes(t map[string]*CIMDatatype, attributes []*CIMAttribute) {
	for _, attr := range attributes {
		if v, ok := t[attr.RDFDomain]; ok {
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

			if types[k].CIMStereotype != "" {
				v.CIMStereotype = types[k].CIMStereotype
			}

			if len(types[k].CIMCategories) > 0 {
				v.CIMCategories = append(v.CIMCategories, types[k].CIMCategories...)
			}

			if types[k].Origin != "" {
				v.Origins = append(v.Origins, types[k].Origin)
			}

			for _, attr := range types[k].Attributes {
				if existingAttrIndex := FindCIMAttributeById(v.Attributes, attr.Id); existingAttrIndex != -1 {
					// If the attribute already exists, we can merge the attributes
					existingAttr := v.Attributes[existingAttrIndex]
					existingAttr.Origins = append(existingAttr.Origins, attr.Origin)
					existingAttr.CIMCategories = append(existingAttr.CIMCategories, attr.CIMCategories...)
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
			if enums[k].CIMStereotype != "" {
				v.CIMStereotype = enums[k].CIMStereotype
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
			if types[k].CIMStereotype != "" {
				v.CIMStereotype = types[k].CIMStereotype
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
			if types[k].CIMStereotype != "" {
				v.CIMStereotype = types[k].CIMStereotype
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
