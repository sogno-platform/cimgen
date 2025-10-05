package cimgen

import (
	"testing"
)

func TestGenerate(t *testing.T) {
	t.Log("Start CIM code generation test")

	cimSpec := NewCIMSpecification()
	cimSpec.ImportCIMSchemaFiles("cgmes_schema/CGMES_3.0.0/IEC61970-600-2_CGMES_3_0_0_RDFS2020_*.rdf")

	genpy := NewCIMGeneratorPython(cimSpec)
	genpy.GenerateType("ACDCTerminal", "cim_generate_test_class.py.log")

	gengo := NewCIMGeneratorGo(cimSpec)
	gengo.GenerateType("ACDCTerminal", "cim_generate_test_struct.go.log")
}
