package cimgen

import (
	"errors"
	"html/template"
	"strings"
)

var (
	ErrValueNotFound = errors.New("value not found")
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
	Category        string
	Stereotype      string
	Origin          string
	RDFRange        string
	RDFDataType     string
	RDFDomain       string
	RDFType         string
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
	Category      string
	Origin        string
	RDFType       string
	Attributes    []*CIMAttribute
}

type CIMEnum struct {
	Id         string
	Label      string
	Namespace  string
	Comment    string
	Stereotype string
	Category   string
	Origin     string
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
		Category:   extractURIEnd(category),
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

func processRDFMap(inputMap map[string]interface{}) (map[string]*CIMType, map[string]*CIMEnum, map[string]*CIMOntology) {
	rdfMap := inputMap["rdf:RDF"].(map[string]interface{})
	descriptions := rdfMap["rdf:Description"].([]map[string]interface{})
	cimTypes := make(map[string]*CIMType, 0)
	cimEnums := make(map[string]*CIMEnum, 0)
	cimEnumValues := make([]*CIMEnumValue, 0)
	cimAttributes := make([]*CIMAttribute, 0)
	cimOntologies := make(map[string]*CIMOntology, 0)

	for _, v := range descriptions {
		objType := extractResource(v, "rdf:type")

		if strings.Contains(objType, "http://www.w3.org/2000/01/rdf-schema#Class") {
			if extractResource(v, "cims:stereotype") == "http://iec.ch/TC57/NonStandard/UML#enumeration" {
				cimEnum := processEnum(v)
				cimEnums[cimEnum.Id] = &cimEnum
			} else {
				cimType := processClass(v)
				cimTypes[cimType.Id] = &cimType
			}
		} else if strings.Contains(objType, "http://www.w3.org/1999/02/22-rdf-syntax-ns#Property") {
			cimAttribute := processProperty(v)
			cimAttributes = append(cimAttributes, &cimAttribute)
		} else if strings.Contains(objType, "http://iec.ch/TC57/1999/rdf-schema-extensions-19990926#ClassCategory") {

		} else if strings.Contains(objType, "http://www.w3.org/2002/07/owl#Ontology") {
			cimOntology := processOntology(v)
			cimOntologies[cimOntology.Keyword] = &cimOntology
		} else {
			cimEnumValue := processEnumValue(v)
			cimEnumValues = append(cimEnumValues, &cimEnumValue)
		}
	}

	for _, attr := range cimAttributes {
		if v, ok := cimTypes[attr.RDFDomain]; ok {
			attr.Category = v.Category
			v.Attributes = append(v.Attributes, attr)
		}
	}

	for _, val := range cimEnumValues {
		if enum, ok := cimEnums[val.RDFType]; ok {
			enum.Values = append(enum.Values, val)
		}
	}

	return cimTypes, cimEnums, cimOntologies
}

func mergeCimTypes(typesMerged map[string]*CIMType, types map[string]*CIMType) map[string]*CIMType {
	for k := range types {
		if v, ok := typesMerged[k]; ok {
			v.Attributes = append(v.Attributes, types[k].Attributes...)
			if types[k].SuperType != "" {
				v.SuperType = types[k].SuperType
				v.Stereotype = types[k].Stereotype
			}
		} else {
			typesMerged[k] = types[k]
		}
	}
	return typesMerged
}
