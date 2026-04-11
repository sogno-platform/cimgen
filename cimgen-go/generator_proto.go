package cimgen

import "strings"

// GenerateProto generates Protocol Buffer source files from the CIM specification.
func (spec *CIMSpecification) GenerateProto(outputDir string) error {
	if err := createOutputDir(outputDir); err != nil {
		return err
	}

	// Rename enum values if they only differ in case from their enum type to avoid conflicts with case-insensitive enums (e.g., protobuf)
	for _, e := range spec.Enums {
		lowerCaseMap := make(map[string][]*CIMEnumValue)
		for _, v := range e.Values {
			lower := strings.ToLower(v.Label)
			lowerCaseMap[lower] = append(lowerCaseMap[lower], v)
		}

		for _, values := range lowerCaseMap {
			if len(values) > 1 {
				for _, v := range values {
					if strings.ToUpper(v.Label) == v.Label {
						v.Label = v.Label + "_u"
					}
				}
			}
		}
	}

	spec.setLangTypesProto()

	if err := generateFiles("proto_struct", ".proto", outputDir, spec.Types); err != nil {
		return err
	}
	if err := generateFiles("proto_enum", ".proto", outputDir, spec.Enums); err != nil {
		return err
	}
	return nil
}

// setLangTypesProto sets default values for attributes based on their data types for Go code generation.
func (cimSpec *CIMSpecification) setLangTypesProto() {
	for _, t := range cimSpec.Types {
		for _, attr := range t.Attributes {
			if attr.UseIDReference {
				attr.LangType = "string"
			} else {
				attr.LangType = MapDataTypeProto(attr.DataType, cimSpec)
			}
		}
	}

	for _, t := range cimSpec.PrimitiveTypes {
		t.LangType = MapDataTypeProto(t.Id, cimSpec)
	}

	for _, t := range cimSpec.CIMDatatypes {
		t.LangType = MapDataTypeProto(t.PrimitiveType, cimSpec)
	}
}

func MapDataTypeProto(s string, cimSpec *CIMSpecification) string {
	switch s {
	case DataTypeString, DataTypeDateTime, DataTypeDate, DataTypeMonthDay:
		return "string"
	case DataTypeBoolean:
		return "bool"
	case DataTypeInteger:
		return "int64"
	case DataTypeFloat, DateTypeDecimal:
		return "double"
	default:
		// if s is a CIMDatatype, return the primitive type
		if _, ok := cimSpec.CIMDatatypes[s]; ok {
			return MapDataTypeProto(cimSpec.CIMDatatypes[s].PrimitiveType, cimSpec)
		}
		// if s is an enum, return the enum name
		if _, ok := cimSpec.Enums[s]; ok {
			return s
		}
		// if s is a class, return the class name
		if _, ok := cimSpec.Types[s]; ok {
			return s
		}
		return s
	}
}
