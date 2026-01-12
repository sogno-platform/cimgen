package cimgen

import (
	"crypto/sha256"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"testing"
)

func TestSchemaImport(t *testing.T) {
	t.Log("Start CIM schema import test")

	output := "cim_schema_import_test.json"
	t.Log("Write imported schema to file:", output)
	f, err := os.Create(output)
	if err != nil {
		t.Error("Cannot create output file:", err)
	}
	defer f.Close()

	// deprecated shema files included in the repo
	//schemaFiles := "cgmes_schema/CGMES_3.0.0/IEC61970-600-2_CGMES_3_0_0_RDFS2020_*.rdf"
	schemaFiles := "../cgmes-application-profiles-library/CGMES/CurrentRelease/RDFS/61970-600-2_*-AP-Voc-RDFS2020.rdf"
	entries, err := filepath.Glob(schemaFiles)
	if err != nil {
		log.Fatal(err)
	}
	t.Log("Read schema files:", entries)

	cimSpec := NewCIMSpecification()
	if err := cimSpec.ImportCIMSchemaFiles(schemaFiles); err != nil {
		t.Fatalf("ImportCIMSchemaFiles failed: %v", err)
	}

	if err := cimSpec.printSpecification(f); err != nil {
		t.Fatalf("printSpecification failed: %v", err)
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
	expectedHash := "93ade55a4fd0d4d61900e819378414a32e1b4e5070a4b4165c501eb4650e1291"
	if fmt.Sprintf("%x", hash) != expectedHash {
		t.Error("decoder tests failed, output file hash does not match expected hash")
	}
}
