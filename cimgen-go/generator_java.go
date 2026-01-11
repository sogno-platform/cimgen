package cimgen

// GenerateJava generates Java source files from the CIM specification.
func (spec *CIMSpecification) GenerateJava(outputDir string) error {
	if err := createOutputDir(outputDir); err != nil {
		return err
	}

	enumOuputDir := outputDir + "/types"
	if err := createOutputDir(enumOuputDir); err != nil {
		return err
	}

	spec.setLangTypesJava()

	if err := generateFiles("java_class", ".java", outputDir, spec.Types); err != nil {
		return err
	}
	if err := generateFiles("java_enum", ".java", enumOuputDir, spec.Enums); err != nil {
		return err
	}
	if err := generateFile("java_constants", "CimConstants.java", outputDir, spec); err != nil {
		return err
	}
	if err := generateFile("java_classlist", "CimClassMap.java", outputDir, spec); err != nil {
		return err
	}
	if err := generateFile("java_profile", "CGMESProfile.java", outputDir, spec); err != nil {
		return err
	}
	return nil
}

// setLangTypesJava sets default values for attributes based on their data types for Java code generation.
func (cimSpec *CIMSpecification) setLangTypesJava() {
	for _, t := range cimSpec.Types {
		for _, attr := range t.Attributes {
			if attr.IsList {
				attr.LangType = "HashSet"
			} else {
				attr.LangType = MapDatatypeJava(attr.DataType)
			}
		}
	}

	for _, t := range cimSpec.PrimitiveTypes {
		t.LangType = MapDatatypeJava(t.Id)
	}

	for _, t := range cimSpec.CIMDatatypes {
		t.LangType = MapDatatypeJava(t.PrimitiveType)
	}
}

func MapDatatypeJava(t string) string {
	switch t {
	case DataTypeString:
		return "String"
	case DataTypeInteger:
		return "Integer"
	case DataTypeBoolean:
		return "Boolean"
	case DataTypeFloat:
		return "Double"
	case DataTypeObject:
		return "Class"
	default:
		return "String"
	}
}
