package cimgen

// GenerateCpp generates C++ source files from the CIM specification.
func (spec *CIMSpecification) GenerateCpp(outputDir string) error {
	if err := createOutputDir(outputDir); err != nil {
		return err
	}

	spec.setLangTypesCpp()
	spec.setDefaultValuesCpp()

	if err := generateFiles("cpp_header", ".hpp", outputDir, spec.Types); err != nil {
		return err
	}
	if err := generateFiles("cpp_object", ".cpp", outputDir, spec.Types); err != nil {
		return err
	}
	if err := generateFiles("cpp_enum_header", ".hpp", outputDir, spec.Enums); err != nil {
		return err
	}
	if err := generateFiles("cpp_enum_object", ".cpp", outputDir, spec.Enums); err != nil {
		return err
	}
	if err := generateFile("cpp_constants_header", "CimConstants.hpp", outputDir, spec); err != nil {
		return err
	}
	if err := generateFile("cpp_constants_object", "CimConstants.cpp", outputDir, spec); err != nil {
		return err
	}
	if err := generateFile("cpp_classlist", "CIMClassList.hpp", outputDir, spec); err != nil {
		return err
	}
	if err := generateFile("cpp_profile_header", "CGMESProfile.hpp", outputDir, spec); err != nil {
		return err
	}
	if err := generateFile("cpp_profile_object", "CGMESProfile.cpp", outputDir, spec); err != nil {
		return err
	}
	if err := generateFile("cpp_iec61970", "IEC61970.hpp", outputDir, spec); err != nil {
		return err
	}
	for _, dt := range spec.CIMDatatypes {
		if err := generateFile("cpp_float_header", dt.Id+".hpp", outputDir, dt); err != nil {
			return err
		}
		if err := generateFile("cpp_float_object", dt.Id+".cpp", outputDir, dt); err != nil {
			return err
		}
	}
	for _, pt := range spec.PrimitiveTypes {
		if pt.Id == "Float" {
			if err := generateFile("cpp_float_header", pt.Id+".hpp", outputDir, pt); err != nil {
				return err
			}
			if err := generateFile("cpp_float_object", pt.Id+".cpp", outputDir, pt); err != nil {
				return err
			}
		} else if pt.Id != "Boolean" && pt.Id != "Integer" {
			if err := generateFile("cpp_string_header", pt.Id+".hpp", outputDir, pt); err != nil {
				return err
			}
			if err := generateFile("cpp_string_object", pt.Id+".cpp", outputDir, pt); err != nil {
				return err
			}
		}
	}
	return nil
}

// setLangTypesCpp sets default values for attributes based on their data types for C++ code generation.
func (cimSpec *CIMSpecification) setLangTypesCpp() {
	for _, t := range cimSpec.Types {
		for _, attr := range t.Attributes {
			if attr.IsList {
				attr.LangType = "std::vector"
			} else {
				attr.LangType = MapDatatypeCpp(attr.DataType)
			}
		}
	}

	for _, t := range cimSpec.PrimitiveTypes {
		t.LangType = MapDatatypeCpp(t.Id)
	}

	for _, t := range cimSpec.CIMDatatypes {
		t.LangType = MapDatatypeCpp(t.PrimitiveType)
	}
}

func MapDatatypeCpp(t string) string {
	switch t {
	case DataTypeString:
		return "std::string"
	case DataTypeInteger:
		return "int"
	case DataTypeBoolean:
		return "bool"
	case DataTypeFloat:
		return "double"
	case DataTypeObject:
		return "Class*"
	default:
		return "std::string"
	}
}

// setDefaultValuesCpp sets default values for attributes based on their data types for C++ code generation.
func (cimSpec *CIMSpecification) setDefaultValuesCpp() {
	for _, t := range cimSpec.Types {
		for _, attr := range t.Attributes {
			if attr.IsList {
				attr.DefaultValue = "{}" // Set default value for list attributes
			} else if attr.IsEnumValue {
				attr.DefaultValue = "0" // Set default value for enum attributes
			} else {
				attr.DefaultValue = MapDefaultValueCpp(attr.DataType)
			}
		}
	}
}

func MapDefaultValueCpp(t string) string {
	switch t {
	case DataTypeString:
		return "\"\""
	case DataTypeInteger:
		return "0"
	case DataTypeBoolean:
		return "false"
	case DataTypeFloat:
		return "0.0"
	case DataTypeObject:
		return "nullptr"
	default:
		return "nullptr"
	}
}
