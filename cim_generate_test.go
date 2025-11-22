package cimgen

import (
	"crypto/sha256"
	"os"
	"testing"
)

func TestGenerate(t *testing.T) {
	t.Log("Start CIM code generation test")

	cimSpec := NewCIMSpecification()
	cimSpec.ImportCIMSchemaFiles("cgmes_schema/CGMES_3.0.0/IEC61970-600-2_CGMES_3_0_0_RDFS2020_*.rdf")

	output := "cim_generate_test_class.py.log"
	t.Log("Write generated python code to file:", output)
	genpy := NewCIMGeneratorPython(cimSpec)
	genpy.GenerateType("ACDCTerminal", "cim_generate_test_class.py.log")

	output = "cim_generate_test_struct.go.log"
	t.Log("Write generated go code to file:", output)
	gengo := NewCIMGeneratorGo(cimSpec)
	gengo.GenerateType("ACDCTerminal", "cim_generate_test_struct.go.log")

	// Compute hash of the output files for verification
	data, err := os.ReadFile("cim_generate_test_class.py.log")
	if err != nil {
		t.Error("Cannot read output file for hashing:", err)
	}
	hash := sha256.Sum256(data)
	t.Logf("SHA256 hash of python output file: %x", hash)

	data, err = os.ReadFile("cim_generate_test_struct.go.log")
	if err != nil {
		t.Error("Cannot read output file for hashing:", err)
	}
	hash = sha256.Sum256(data)
	t.Logf("SHA256 hash of go output file: %x", hash)
}
