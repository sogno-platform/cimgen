package cimgen

import (
	"bytes"
	"encoding/json"
	"fmt"
	"html/template"
	"io"
	"os"
	"path/filepath"
	"sort"
	"strings"
)

// enum to determine primitve types
const (
	DataTypeString   = "String"
	DataTypeInteger  = "Integer"
	DataTypeBoolean  = "Boolean"
	DataTypeFloat    = "Float"
	DataTypeDate     = "Date"
	DataTypeTime     = "Time"
	DataTypeDateTime = "DateTime"
	DataTypeBinary   = "Binary"
	DataTypeEnum     = "Enum"
	DataTypeObject   = "Object"
	DataTypeList     = "List"
	DataTypeUnknown  = "Unknown"
)

// CIMAttribute represents a CIM attribute with its properties.
type CIMAttribute struct {
	Id              string
	Label           string
	Namespace       string
	Comment         string
	IsList          bool
	AssociationUsed bool
	IsFixed         bool
	InverseRole     string
	Categories      []string
	Stereotype      string
	Origin          string
	Origins         []string
	Range           string
	DataType        string
	IsPrimitive     bool
	RDFDomain       string
	RDFType         string
	DefaultValue    string
	IsUsed          bool
	IsEnumValue     bool
}

// CIMType represents a CIM class/type with its properties and attributes.
type CIMType struct {
	Id            string
	Label         string
	Namespace     string
	Comment       string
	SuperType     string
	SuperTypes    []string
	SubClasses    []string
	EnumInstances []string
	Stereotype    string
	Categories    []string
	Origin        string
	Origins       []string
	RDFType       string
	Attributes    []*CIMAttribute
}

// CIMEnum represents a CIM enumeration with its values.
type CIMEnum struct {
	Id         string
	Label      string
	Namespace  string
	Comment    string
	Stereotype string
	Origin     string
	Origins    []string
	RDFType    string
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
}

// CIMSpecification represents the entire CIM specification with types, enums, and ontologies.
type CIMSpecification struct {
	Types      map[string]*CIMType
	Enums      map[string]*CIMEnum
	Ontologies map[string]*CIMOntology
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

// processClass processes a map representing a CIM class and returns a CIMType struct.
func processClass(classMap map[string]interface{}) CIMType {

	typeId := extractValue(classMap, "@rdf:about")
	label := extractText(classMap, "rdfs:label")
	superType := extractResource(classMap, "rdfs:subClassOf")
	comment := extractText(classMap, "rdfs:comment")
	stereotype := extractStringOrResource(classMap["cims:stereotype"])
	category := extractResource(classMap, "cims:belongsToCategory")
	rdfType := extractResource(classMap, "rdf:type")

	comment = strings.Join(strings.Fields(template.HTMLEscapeString(comment)), " ")

	return CIMType{
		Id:         extractURIEnd(typeId),
		Label:      label,
		SuperType:  extractURIEnd(superType),
		Comment:    comment,
		Namespace:  extractURIPath(typeId),
		Stereotype: extractURIEnd(stereotype),
		RDFType:    extractURIEnd(rdfType),
		Categories: []string{extractURIEnd(category)},
		Attributes: make([]*CIMAttribute, 0),
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

	comment = strings.Join(strings.Fields(template.HTMLEscapeString(comment)), " ")

	associationUsed := false
	if extractStringOrResource(classMap["cims:AssociationUsed"]) == "Yes" {
		associationUsed = true
	}

	isList := false
	multiplicity := extractResource(classMap, "cims:multiplicity")
	if multiplicity == "http://iec.ch/TC57/1999/rdf-schema-extensions-19990926#M:0..n" || multiplicity == "http://iec.ch/TC57/1999/rdf-schema-extensions-19990926#M:1..n" {
		isList = true
	}

	return CIMAttribute{
		Id:              extractURIEnd(attrId),
		Comment:         comment,
		Stereotype:      extractURIEnd(stereotype),
		Namespace:       extractURIPath(attrId),
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

// processEnum processes a map representing a CIM enumeration and returns a CIMEnum struct.
func processEnum(classMap map[string]interface{}) CIMEnum {

	typeId := extractValue(classMap, "@rdf:about")
	label := extractText(classMap, "rdfs:label")
	comment := extractText(classMap, "rdfs:comment")
	stereotype := extractStringOrResource(classMap["cims:stereotype"])
	rdfType := extractResource(classMap, "rdf:type")

	return CIMEnum{
		Id:         extractURIEnd(typeId),
		Label:      label,
		Comment:    comment,
		Namespace:  extractURIPath(typeId),
		Stereotype: extractURIEnd(stereotype),
		RDFType:    extractURIEnd(rdfType),
	}
}

// processEnumValue processes a map representing a CIM enumeration value and returns a CIMEnumValue struct.
func processEnumValue(classMap map[string]interface{}) CIMEnumValue {

	typeId := extractValue(classMap, "@rdf:about")
	label := extractText(classMap, "rdfs:label")
	comment := extractText(classMap, "rdfs:comment")
	stereotype := extractStringOrResource(classMap["cims:stereotype"])
	rdfType := extractResource(classMap, "rdf:type")

	return CIMEnumValue{
		Id:         extractURIEnd(typeId),
		Label:      label,
		Comment:    comment,
		Stereotype: extractURIEnd(stereotype),
		RDFType:    extractURIEnd(rdfType),
	}
}

// processOntology processes a map representing a CIM ontology and returns a CIMOntology struct.
func processOntology(classMap map[string]interface{}) CIMOntology {

	typeId := extractValue(classMap, "@rdf:about")
	rdfType := extractResource(classMap, "rdf:type")
	versionIRI := extractResource(classMap, "owl:versionIRI")
	versionInfo := extractText(classMap, "owl:versionInfo")
	keyword := extractValue(classMap, "dcat:keyword")

	return CIMOntology{
		Id:          extractURIEnd(typeId),
		Namespace:   extractURIPath(typeId),
		RDFType:     extractURIEnd(rdfType),
		VersionIRI:  versionIRI,
		VersionInfo: versionInfo,
		Keyword:     keyword,
	}
}

// processRDFMap processes the RDF map and extracts CIM types, enums, and ontology.
func processRDFMap(inputMap map[string]interface{}) (map[string]*CIMType, map[string]*CIMEnum, CIMOntology) {
	rdfMap := inputMap["rdf:RDF"].(map[string]interface{})
	descriptions := rdfMap["rdf:Description"].([]map[string]interface{})
	cimTypes := make(map[string]*CIMType, 0)
	cimEnums := make(map[string]*CIMEnum, 0)
	cimEnumValues := make([]*CIMEnumValue, 0)
	cimAttributes := make([]*CIMAttribute, 0)
	var cimOntology CIMOntology

	for _, v := range descriptions {
		objType := extractResource(v, "rdf:type")

		if strings.Contains(objType, "http://www.w3.org/2000/01/rdf-schema#Class") {
			if extractResource(v, "cims:stereotype") == "http://iec.ch/TC57/NonStandard/UML#enumeration" {
				cimEnum := processEnum(v)
				cimEnum.Origin = cimOntology.Keyword
				cimEnum.Origins = []string{cimOntology.Keyword}
				cimEnums[cimEnum.Id] = &cimEnum
			} else {
				cimType := processClass(v)
				cimType.Origin = cimOntology.Keyword
				cimType.Origins = []string{cimOntology.Keyword}
				cimTypes[cimType.Id] = &cimType
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

	return cimTypes, cimEnums, cimOntology
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
func mergeCimEnums(typesMerged map[string]*CIMEnum, types map[string]*CIMEnum) map[string]*CIMEnum {
	for k := range types {
		if v, ok := typesMerged[k]; ok {
			if types[k].Stereotype != "" {
				v.Stereotype = types[k].Stereotype
			}

			if types[k].Origin != "" {
				v.Origins = append(v.Origins, types[k].Origin)
			}

			for _, val := range types[k].Values {
				if existingValIndex := FindCIMEnumValueById(v.Values, val.Id); existingValIndex == -1 {
					v.Values = append(v.Values, val)
				}
			}
		} else {
			typesMerged[k] = types[k]
		}
	}
	return typesMerged
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

// pickMainOrigin selects the main origin for each CIMType based on the Origins field of the attributes.
// The origin that appears most frequently in the Origins field of the attributes is selected as the main origin.
// If there is a tie, the first origin in the list is selected.
// Only the attributes are considered that have more than one entry in the Origins field.
// If "EQ" is among the most frequent origins, it is selected as the main origin.
// Otherwise, the first origin in alphabetical order is selected.
// This function updates the Origin field of each CIMType accordingly.
func (cimSpec *CIMSpecification) pickMainOrigin() {
	for _, t := range cimSpec.Types {

		originCount := make(map[string]int)
		tmpType := t
		id := t.Id
		for id != "" {
			for _, attr := range tmpType.Attributes {
				if len(attr.Origins) > 1 {
					for _, origin := range attr.Origins {
						if contains(t.Origins, origin) {
							originCount[origin]++
						}

					}
				}
			}
			// Move to the super type to check its attributes
			if tmpType.SuperType != "" {
				if superType, ok := cimSpec.Types[tmpType.SuperType]; ok {
					tmpType = superType
					id = tmpType.Id
				} else {
					break
				}
			} else {
				break
			}
		}
		//fmt.Println("Origin count map:", originCount, "for type", t.Id)

		filteredOrigins := make([]string, 0, len(t.Origins))
		if len(originCount) > 0 {
			maxCount := 0
			for _, count := range originCount {
				if count > maxCount {
					maxCount = count
				}
			}

			for origin, count := range originCount {
				if count == maxCount {
					filteredOrigins = append(filteredOrigins, origin)
				}
			}
		} else {
			filteredOrigins = t.Origins
		}

		if contains(filteredOrigins, "EQ") {
			t.Origin = "EQ"
		} else {
			sort.Strings(filteredOrigins)
			t.Origin = filteredOrigins[0]
		}
	}
}

// contains checks if a string slice contains a specific string.
func contains(slice []string, str string) bool {
	for _, v := range slice {
		if v == str {
			return true
		}
	}
	return false
}

// NewCIMSpecification creates and returns a new CIMSpecification instance.
func NewCIMSpecification() *CIMSpecification {
	return &CIMSpecification{
		Types:      make(map[string]*CIMType, 0),
		Enums:      make(map[string]*CIMEnum, 0),
		Ontologies: make(map[string]*CIMOntology, 0),
	}
}

// addRDFMap adds the CIM types, enums, and ontology from the input map to the CIMSpecification.
func (cimSpec *CIMSpecification) addRDFMap(inputMap map[string]interface{}) {
	cimTypes, cimEnums, cimOntology := processRDFMap(inputMap)
	cimSpec.Types = mergeCimTypes(cimSpec.Types, cimTypes)
	cimSpec.Enums = mergeCimEnums(cimSpec.Enums, cimEnums)
	cimSpec.Ontologies[cimOntology.Keyword] = &cimOntology
}

// sortAttributes sorts the attributes of each CIMType by their Id.
func (cimSpec *CIMSpecification) sortAttributes() {
	for _, t := range cimSpec.Types {
		sort.Slice(t.Attributes, func(i, j int) bool {
			return t.Attributes[i].Id < t.Attributes[j].Id
		})
	}
}

// determineDataTypes determines the data types of attributes and marks them as primitive if applicable.
func (cimSpec *CIMSpecification) determineDataTypes() {
	for _, t := range cimSpec.Types {
		for _, attr := range t.Attributes {
			if isDataType(attr.DataType) {
				attr.IsPrimitive = true
			} else if attr.DataType == "" {
				attr.DataType = DataTypeObject
				attr.IsPrimitive = false
			}
		}
	}
}

// isDataType checks if the given type string is a known data type.
func isDataType(typeStr string) bool {
	switch typeStr {
	case DataTypeString, DataTypeInteger, DataTypeBoolean,
		DataTypeFloat, DataTypeDate, DataTypeTime,
		DataTypeDateTime, DataTypeBinary:
		return true
	default:
		return false
	}
}

// setDefaultValuesPython sets default values for attributes based on their data types for Python code generation.
func (cimSpec *CIMSpecification) setDefaultValuesPython() {
	for _, t := range cimSpec.Types {
		for _, attr := range t.Attributes {
			if attr.IsList {
				attr.DefaultValue = "[]" // Set default value for list attributes
			} else if attr.DataType == DataTypeString {
				attr.DefaultValue = "''" // Set default value for string attributes
			} else if attr.DataType == DataTypeInteger {
				attr.DefaultValue = "0" // Set default value for integer attributes
			} else if attr.DataType == DataTypeBoolean {
				attr.DefaultValue = "False" // Set default value for boolean attributes
			} else if attr.DataType == DataTypeFloat {
				attr.DefaultValue = "0.0" // Set default value for float attributes
			} else if attr.DataType == DataTypeObject {
				attr.DefaultValue = "None" // Set default value for object attributes
			}
		}
	}
}

// fixMissingMRIDs adds missing MRID attributes to types that should have them.
func (cimSpec *CIMSpecification) fixMissingMRIDs() {
	for _, t := range cimSpec.Types {
		if (t.Stereotype == "concrete" || t.Stereotype == "") && t.SuperType == "" && t.Id != "IdentifiedObject" {
			t.Attributes = append(t.Attributes, &CIMAttribute{
				Id:              "MRID",
				Label:           "mRID",
				Namespace:       "",
				Comment:         "Master resource identifier issued by a model authority. The mRID is unique within an exchange context. Global uniqueness is easily achieved by using a UUID, as specified in RFC 4122, for the mRID. The use of UUID is strongly recommended. For CIMXML data files in RDF syntax conforming to IEC 61970-552, the mRID is mapped to rdf:ID or rdf:about attributes that identify CIM object elements.",
				IsList:          false,
				AssociationUsed: false,
				IsFixed:         false,
				InverseRole:     "",
				Stereotype:      "attribute",
				Range:           "",
				DataType:        "String",
				IsPrimitive:     true,
				RDFDomain:       "",
				RDFType:         "Property",
				DefaultValue:    "''",
			})
			fmt.Println("Added missing MRID to type", t.Id)
		}
	}
}

// markUnusedAttributesAndAssociations marks attributes and associations as unused if they are not used.
func (cimSpec *CIMSpecification) markUnusedAttributesAndAssociations() {
	for _, t := range cimSpec.Types {
		for _, attr := range t.Attributes {
			attr.IsUsed = true
			if !attr.AssociationUsed {
				if attr.DataType == DataTypeObject {
					if attr.IsList {
						attr.IsUsed = false
						fmt.Println("Marked unused list association", t.Id+"."+attr.Id, "of type", attr.Range)
					}
				} else {
					attr.IsPrimitive = true
					fmt.Println("Replaced association with primitive", t.Id+"."+attr.Id, "of type", attr.DataType)
				}
			}
		}
	}
}

// removeIdentifiedObjectAttributes renames attributes named "IdentifiedObject" to avoid conflicts.
func (cimSpec *CIMSpecification) removeIdentifiedObjectAttributes() {
	for _, t := range cimSpec.Types {
		for _, attr := range t.Attributes {
			if attr.Label == "IdentifiedObject" {
				attr.Label = t.Label + "IdentifiedObject"
				fmt.Println("Renamed IdentifiedObject attribute to", attr.Label, "in type", t.Id)
			}
		}
	}
}

// findEnumAttributes marks attributes as enum values if their range corresponds to a known enumeration.
func (cimSpec *CIMSpecification) findEnumAttributes() {
	for _, t := range cimSpec.Types {
		for _, attr := range t.Attributes {
			if _, ok := cimSpec.Enums[attr.Range]; ok {
				attr.IsEnumValue = true
			}
		}
	}
}

// postprocess performs various post-processing steps on the CIMSpecification.
func (cimSpec *CIMSpecification) postprocess() {
	cimSpec.pickMainOrigin()
	cimSpec.sortAttributes()
	cimSpec.determineDataTypes()
	cimSpec.setDefaultValuesPython()
	cimSpec.fixMissingMRIDs()
	cimSpec.markUnusedAttributesAndAssociations()
	cimSpec.removeIdentifiedObjectAttributes()
	cimSpec.findEnumAttributes()
}

// printSpecification prints the CIMSpecification to the provided writer in JSON format.
func (cimSpec *CIMSpecification) printSpecification(w io.Writer) {
	jsonb, err := json.MarshalIndent(cimSpec.Ontologies, "", "  ")
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
