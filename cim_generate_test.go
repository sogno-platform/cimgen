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

	outputDir := "cimgostructs"
	cimSpec.GenerateGo(outputDir)

	// Compute hash of the output files for verification
	data, err := os.ReadFile(outputDir + "ACLineSegment.go")
	if err != nil {
		t.Error("Cannot read output file for hashing:", err)
	}
	hash := sha256.Sum256(data)
	t.Logf("SHA256 hash of output file: %x", hash)
}
