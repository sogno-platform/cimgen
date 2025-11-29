package cimgen

import (
	"crypto/sha256"
	"fmt"
	"os"
	"testing"
)

func TestSchemaImport(t *testing.T) {
	t.Log("Start CIM schema import test")

	output := "cim_schema_import_test.log"
	t.Log("Write imported schema to file:", output)
	f, err := os.Create(output)
	if err != nil {
		t.Error("Cannot create output file:", err)
	}
	defer f.Close()

	cimSpec := NewCIMSpecification()
	cimSpec.ImportCIMSchemaFiles("cgmes_schema/CGMES_3.0.0/IEC61970-600-2_CGMES_3_0_0_RDFS2020_*.rdf")

	cimSpec.printSpecification(f)

	if cimSpec.Ontologies["DL"].Keyword != "DL" {
		t.Error("cim schema test failed, expected Ontology DL")
	}

	// Compute hash of the output file for verification
	f.Sync()
	data, err := os.ReadFile(output)
	if err != nil {
		t.Error("Cannot read output file for hashing:", err)
	}
	hash := sha256.Sum256(data)
	t.Logf("SHA256 hash of output file: %x", hash)

	// Test output file against expected hash
	expectedHash := "010441b8bba6970ef068a6bad54e78edf57bbdce3eba3ec9dad7263acbbe246e" // SHA256 of empty file
	if fmt.Sprintf("%x", hash) != expectedHash {
		t.Error("decoder tests failed, output file hash does not match expected hash")
	}
}
