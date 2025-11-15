package cimgostructs

type CIMTypeInfo struct {
	Id         string
	Label      string
	Namespace  string
	Comment    string
	SuperType  string
	Origin     string
	Origins    []string
	Attributes map[string]CIMAttributeInfo
}

type CIMAttributeInfo struct {
	Id              string
	Label           string
	Namespace       string
	Comment         string
	IsList          bool
	AssociationUsed bool
	IsFixed         bool
	InverseRole     string
	Origin          string
	Range           string
	DataType        string
	IsPrimitive     bool
	DefaultValue    string
	IsUsed          bool
	IsEnumValue     bool
}
