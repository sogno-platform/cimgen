package cimgen

// GenerateJS generates JavaScript source files from the CIM specification.
func (spec *CIMSpecification) GenerateJS(outputDir string) error {
	if err := createOutputDir(outputDir); err != nil {
		return err
	}

	// TODO spec.setLangTypesJS()

	if err := generateFiles("js_class", ".js", outputDir, spec.Types); err != nil {
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
