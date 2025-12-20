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
	schemaFiles := "cgmes-application-profiles-library/CGMES/CurrentRelease/RDFS/61970-600-2_*-AP-Voc-RDFS2020.rdf"
	entries, err := filepath.Glob(schemaFiles)
	if err != nil {
		log.Fatal(err)
	}
	t.Log("Read schema files:", entries)

	cimSpec := NewCIMSpecification()
	cimSpec.ImportCIMSchemaFiles(schemaFiles)

	cimSpec.printSpecification(f)

	// Compute hash of the output file for verification
	f.Sync()
	data, err := os.ReadFile(output)
	if err != nil {
		t.Error("Cannot read output file for hashing:", err)
	}
	hash := sha256.Sum256(data)
	t.Logf("SHA256 hash of output file: %x", hash)

	// Test output file against expected hash
	expectedHash := "8de9c520a3e1a1ee3c5490829c29097d4cd4ccb47d8f1322a9040bbb43fb943e"
	if fmt.Sprintf("%x", hash) != expectedHash {
		t.Error("decoder tests failed, output file hash does not match expected hash")
	}
}
