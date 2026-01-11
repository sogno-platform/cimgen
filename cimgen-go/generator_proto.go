package cimgen

// GenerateProto generates Protocol Buffer source files from the CIM specification.
func (spec *CIMSpecification) GenerateProto(outputDir string) error {
	if err := createOutputDir(outputDir); err != nil {
		return err
	}

	if err := generateFiles("proto_struct", ".proto", outputDir, spec.Types); err != nil {
		return err
	}
	return nil
}
