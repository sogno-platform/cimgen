package cimgen

// GenerateGo generates Go source files from the CIM specification.
func (spec *CIMSpecification) GenerateGo(outputDir string) error {
	if err := createOutputDir(outputDir); err != nil {
		return err
	}

	spec.setLangTypesGo()

	if err := generateFiles("go_struct", ".go", outputDir, spec.Types); err != nil {
		return err
	}
	if err := generateFile("go_struct_lists", "cim_struct_lists.go", outputDir, spec); err != nil {
		return err
	}
	if err := generateFiles("go_enum", ".go", outputDir, spec.Enums); err != nil {
		return err
	}
	if err := generateFiles("go_type_alias", ".go", outputDir, spec.CIMDatatypes); err != nil {
		return err
	}
	if err := generateFile("go_constants", "cim_constants.go", outputDir, spec); err != nil {
		return err
	}
	return nil
}

// setLangTypesGo sets default values for attributes based on their data types for Go code generation.
func (cimSpec *CIMSpecification) setLangTypesGo() {
	for _, t := range cimSpec.Types {
		for _, attr := range t.Attributes {
			if attr.IsList {
				attr.LangType = "[]" + MapDataTypeGo(attr.DataType)
			} else {
				attr.LangType = MapDataTypeGo(attr.DataType)
			}
		}
	}

	for _, t := range cimSpec.PrimitiveTypes {
		t.LangType = MapDataTypeGo(t.Id)
	}

	for _, t := range cimSpec.CIMDatatypes {
		t.LangType = MapDataTypeGo(t.PrimitiveType)
	}
}

func MapDataTypeGo(s string) string {
	switch s {
	case DataTypeString:
		return "string"
	case DataTypeBoolean:
		return "bool"
	case DataTypeInteger:
		return "int"
	case DataTypeFloat:
		return "float64"
	case DataTypeDateTime:
		return "string"
	default:
		return "string"
	}
}
