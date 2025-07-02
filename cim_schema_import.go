package cimgen

import (
	"encoding/json"
	"errors"
	"fmt"
	"html/template"
	"io"
	"sort"
	"strings"
)

var (
	ErrValueNotFound = errors.New("value not found")
)

// enum to determine primitve types
const (
	PrimitiveTypeString   = "String"
	PrimitiveTypeInteger  = "Integer"
	PrimitiveTypeBoolean  = "Boolean"
	PrimitiveTypeFloat    = "Float"
	PrimitiveTypeDate     = "Date"
	PrimitiveTypeTime     = "Time"
	PrimitiveTypeDateTime = "DateTime"
	PrimitiveTypeBinary   = "Binary"
	PrimitiveTypeEnum     = "Enum"
	PrimitiveTypeObject   = "Object"
	PrimitiveTypeList     = "List"
	PrimitiveTypeUnknown  = "Unknown"
)

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
	RDFRange        string
	RDFDataType     string
	RDFDomain       string
	RDFType         string
	PrimitiveType   string
	DefaultValue    string
}

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

type CIMEnumValue struct {
	Id         string
	Label      string
	Comment    string
	Stereotype string
	RDFType    string
}

type CIMOntology struct {
	Id          string
	Namespace   string
	VersionIRI  string
	VersionInfo string
	Keyword     string
	RDFType     string
}

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

func extractText(obj map[string]interface{}, key string) string {
	if v, ok := obj[key]; ok {
		if m, ok := v.(map[string]interface{}); ok {
			return m["_"].(string)
		}
	}
	return ""
}

func extractValue(obj map[string]interface{}, key string) string {
	if t, ok := obj[key]; ok {
		return t.(string)
	}
	return ""
}

func extractURIEnd(uri string) string {
	l := strings.Split(uri, "#")
	return l[len(l)-1]
}

func extractURIPath(uri string) string {
	l := strings.Split(uri, "#")
	return l[0]
}

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

func processProperty(classMap map[string]interface{}) CIMAttribute {
	attrId := extractValue(classMap, "@rdf:about")
	rdfType := extractResource(classMap, "rdf:type")
	comment := extractText(classMap, "rdfs:comment")
	stereotype := extractStringOrResource(classMap["cims:stereotype"])
	label := extractText(classMap, "rdfs:label")
	domain := extractResource(classMap, "rdfs:domain")
	dataType := extractResource(classMap, "cims:dataType")
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
		RDFDomain:       extractURIEnd(domain),
		RDFDataType:     extractURIEnd(dataType),
		RDFRange:        extractURIEnd(rdfRange),
		RDFType:         extractURIEnd(rdfType),
		AssociationUsed: associationUsed,
		InverseRole:     extractURIEnd(inverseRoleName),
		IsList:          isList,
	}
}

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

	for _, attr := range cimAttributes {
		if v, ok := cimTypes[attr.RDFDomain]; ok {
			attr.Categories = v.Categories
			v.Attributes = append(v.Attributes, attr)
		}
	}

	for _, val := range cimEnumValues {
		if enum, ok := cimEnums[val.RDFType]; ok {
			enum.Values = append(enum.Values, val)
		}
	}

	return cimTypes, cimEnums, cimOntology
}

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
func (cimSpec *CIMSpecification) pickMainOrigin() {
	for _, t := range cimSpec.Types {
		if len(t.Attributes) == 0 {
			continue
		}

		originCount := make(map[string]int)
		tmpType := t
		id := t.Id
		for id != "" {
			for _, attr := range tmpType.Attributes {
				if len(attr.Origins) > 1 {
					for _, origin := range attr.Origins {
						originCount[origin]++
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

		var mainOrigin string
		maxCount := 0
		// If EQ is in the origin count, we set it as the main origin if no other origin has a higher count.
		if v, ok := originCount["EQ"]; ok {
			maxCount = v
			mainOrigin = "EQ"
		}

		for origin, count := range originCount {
			if count > maxCount || (count == maxCount && mainOrigin == "") {
				mainOrigin = origin
				maxCount = count
			}
		}

		if mainOrigin != "" {
			t.Origin = mainOrigin
		} else {
			// If no main origin was found, we can set the origin to the first one
			// in the list of Origins of the type ordered in alphabetical order.
			sort.Strings(t.Origins)
			if len(t.Origins) > 0 {
				t.Origin = t.Origins[0]
			}
			// If EQ is in the list of Origins of type t, we can set it as the origin.
			if contains(t.Origins, "EQ") {
				t.Origin = "EQ"
			}
		}

	}
}

func contains(slice []string, str string) bool {
	for _, v := range slice {
		if v == str {
			return true
		}
	}
	return false
}

func findDuplicateAttributes(types map[string]*CIMType) {
	for k := range types {
		if t, ok := types[k]; ok {
			for i, attr := range t.Attributes {
				for j, attrsec := range t.Attributes {
					if attrsec.Id == attr.Id && i != j {
						fmt.Println("Duplicate attribute", attrsec.Id, "in type", t.Id)
					}
				}
			}
		}
	}
}

func newCIMSpecification() *CIMSpecification {
	return &CIMSpecification{
		Types:      make(map[string]*CIMType, 0),
		Enums:      make(map[string]*CIMEnum, 0),
		Ontologies: make(map[string]*CIMOntology, 0),
	}
}

func (cimSpec *CIMSpecification) addRDFMap(inputMap map[string]interface{}) {
	cimTypes, cimEnums, cimOntology := processRDFMap(inputMap)
	cimSpec.Types = mergeCimTypes(cimSpec.Types, cimTypes)
	cimSpec.Enums = mergeCimEnums(cimSpec.Enums, cimEnums)
	cimSpec.Ontologies[cimOntology.Keyword] = &cimOntology
}

func (cimSpec *CIMSpecification) sortAttributes() {
	for _, t := range cimSpec.Types {
		sort.Slice(t.Attributes, func(i, j int) bool {
			return t.Attributes[i].Id < t.Attributes[j].Id
		})
		//slices.SortFunc(t.Attributes, func(a, b *CIMAttribute) int {
		//	return strings.Compare(a.Id, b.Id)
		//})
	}
}

func (cimSpec *CIMSpecification) determinePrimitiveTypes() {
	for _, t := range cimSpec.Types {
		for _, attr := range t.Attributes {
			if isPrimitiveType(attr.RDFDataType) {
				attr.PrimitiveType = attr.RDFDataType
			} else if attr.RDFDataType == "" {
				attr.PrimitiveType = PrimitiveTypeObject
			}
		}
	}
}

// isPrimitiveType checks if the given type string is a known primitive type.
func isPrimitiveType(typeStr string) bool {
	switch typeStr {
	case PrimitiveTypeString, PrimitiveTypeInteger, PrimitiveTypeBoolean,
		PrimitiveTypeFloat, PrimitiveTypeDate, PrimitiveTypeTime,
		PrimitiveTypeDateTime, PrimitiveTypeBinary:
		return true
	default:
		return false
	}
}

func (cimSpec *CIMSpecification) setDefaultValuesPython() {
	for _, t := range cimSpec.Types {
		for _, attr := range t.Attributes {
			if attr.IsList {
				attr.DefaultValue = "[]" // Set default value for list attributes
			} else if attr.PrimitiveType == PrimitiveTypeString {
				attr.DefaultValue = "''" // Set default value for string attributes
			} else if attr.PrimitiveType == PrimitiveTypeInteger {
				attr.DefaultValue = "0" // Set default value for integer attributes
			} else if attr.PrimitiveType == PrimitiveTypeBoolean {
				attr.DefaultValue = "False" // Set default value for boolean attributes
			} else if attr.PrimitiveType == PrimitiveTypeFloat {
				attr.DefaultValue = "0.0" // Set default value for float attributes
			} else if attr.PrimitiveType == PrimitiveTypeObject {
				attr.DefaultValue = "None" // Set default value for object attributes
			}
		}
	}
}

func (cimSpec *CIMSpecification) postprocess() {
	cimSpec.pickMainOrigin()
	cimSpec.sortAttributes()
	cimSpec.determinePrimitiveTypes()
	cimSpec.setDefaultValuesPython()
}

func (cimSpec *CIMSpecification) printSpecification(w io.Writer) {
	fmt.Fprintln(w, "CIM Specification:")

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
