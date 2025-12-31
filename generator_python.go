package cimgen

// GeneratePython generates Python source files from the CIM specification.
func (spec *CIMSpecification) GeneratePython(outputDir string) error {
	if err := createOutputDir(outputDir); err != nil {
		return err
	}

	spec.setLangTypesPython()
	spec.setDefaultValuesPython()

	if err := generateFiles("python_class", ".py", outputDir, spec.Types); err != nil {
		return err
	}
	if err := generateFile("python_constants", "cim_constants.py", outputDir, spec); err != nil {
		return err
	}
	if err := generateFile("python_profile", "cim_profiles.py", outputDir, spec); err != nil {
		return err
	}
	if err := generateFiles("python_datatype", ".py", outputDir, spec.CIMDatatypes); err != nil {
		return err
	}
	if err := generateFiles("python_enum", ".py", outputDir, spec.Enums); err != nil {
		return err
	}
	if err := generateFiles("python_primitive", ".py", outputDir, spec.PrimitiveTypes); err != nil {
		return err
	}
	return nil
}

// GeneratePythonSimple generates simple Python source files from the CIM specification.
func (spec *CIMSpecification) GeneratePythonSimple(outputDir string) error {
	if err := createOutputDir(outputDir); err != nil {
		return err
	}

	spec.setLangTypesPython()
	spec.setDefaultValuesPython()

	if err := generateFiles("python_simple_class", ".py", outputDir, spec.Types); err != nil {
		return err
	}
	if err := generateFile("python_constants", "CimConstants.py", outputDir, spec); err != nil {
		return err
	}
	if err := generateFile("python_simple_profiles", "CGMESProfile.py", outputDir, spec); err != nil {
		return err
	}
	return nil
}

// setLangTypesPython sets default values for attributes based on their data types for Go code generation.
func (cimSpec *CIMSpecification) setLangTypesPython() {
	for _, t := range cimSpec.Types {
		for _, attr := range t.Attributes {
			if attr.IsList {
				attr.LangType = "list"
			} else {
				attr.LangType = MapDatatypePython(attr.DataType)
			}
		}
	}

	for _, t := range cimSpec.PrimitiveTypes {
		t.LangType = MapDatatypePython(t.Id)
	}

	for _, t := range cimSpec.CIMDatatypes {
		t.LangType = MapDatatypePython(t.PrimitiveType)
	}
}

func MapDatatypePython(t string) string {
	switch t {
	case DataTypeString, DataTypeDateTime, DataTypeDate:
		return "str"
	case DataTypeInteger:
		return "int"
	case DataTypeBoolean:
		return "bool"
	case DataTypeFloat:
		return "float"
	case DataTypeObject:
		return "Optional[str]"
	default:
		return "str"
	}
}

// setDefaultValuesPython sets default values for attributes based on their data types for Python code generation.
func (cimSpec *CIMSpecification) setDefaultValuesPython() {
	for _, t := range cimSpec.Types {
		for _, attr := range t.Attributes {
			if attr.IsList {
				attr.DefaultValue = "list" // Set default value for list attributes
			} else {
				attr.DefaultValue = MapDefaultValuePython(attr.DataType)
			}
		}
	}
}

func MapDefaultValuePython(t string) string {
	switch t {
	case DataTypeString, DataTypeDateTime, DataTypeDate:
		return "\"\""
	case DataTypeInteger:
		return "0"
	case DataTypeBoolean:
		return "False"
	case DataTypeFloat:
		return "0.0"
	case DataTypeObject:
		return "None"
	default:
		return "\"\""
	}
}
