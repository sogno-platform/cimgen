package cimgen

import (
	"crypto/sha256"
	"os"
	"testing"
)

func TestGenerate(t *testing.T) {
	t.Log("Start CIM code generation test")

	cimSpec := NewCIMSpecification()
	err := cimSpec.ImportCIMSchemaFiles("cgmes-application-profiles-library/CGMES/CurrentRelease/RDFS/61970-600-2_*-AP-Voc-RDFS2020.rdf")
	if err != nil {
		t.Fatalf("ImportCIMSchemaFiles failed: %v", err)
	}

	outputDir := "test-output"
	err = cimSpec.GenerateGo(outputDir)
	if err != nil {
		t.Fatalf("GenerateGo failed: %v", err)
	}

	// Compute hash of the output files for verification
	data, err := os.ReadFile(outputDir + "/ACLineSegment.go")
	if err != nil {
		t.Error("Cannot read output file for hashing:", err)
	}
	hash := sha256.Sum256(data)
	t.Logf("SHA256 hash of output file: %x", hash)
}
