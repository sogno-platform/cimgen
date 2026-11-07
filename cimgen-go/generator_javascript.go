package cimgen

// GenerateJavaScript generates JavaScript source files from the CIM specification.
func (spec *CIMSpecification) GenerateJavaScript(outputDir string) error {
	if err := cleanAllRecursively(outputDir); err != nil {
		return err
	}

	if err := createOutputDir(outputDir); err != nil {
		return err
	}

	// TODO spec.setLangTypesJS()

	if err := generateFiles("js_class", ".js", outputDir, spec.Types); err != nil {
		return err
	}
	if err := generateFiles("js_datatype", ".js", outputDir, spec.CIMDatatypes); err != nil {
		return err
	}
	if err := generateFiles("js_enum", ".js", outputDir, spec.Enums); err != nil {
		return err
	}
	primitiveTypes := make(map[string]*CIMPrimitive, len(spec.PrimitiveTypes))
	for k, t := range spec.PrimitiveTypes {
		if t.Id != "String" {
			primitiveTypes[k] = t
		}
	}
	if err := generateFiles("js_primitive", ".js", outputDir, primitiveTypes); err != nil {
		return err
	}
	if err := generateFile("js_constants", "CimConstants.js", outputDir, spec); err != nil {
		return err
	}
	if err := generateFile("js_baseclass", "BaseClass.js", outputDir, spec); err != nil {
		return err
	}
	if err := generateFile("js_profile", "CGMESProfile.js", outputDir, spec); err != nil {
		return err
	}
	return nil
}
