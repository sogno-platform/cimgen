package cimgen

import (
	"crypto/sha256"
	"fmt"
	"os"
	"testing"
)

func TestSchemaImportCGMES2(t *testing.T) {
	testSchemaImport(t, CGMES2, CGMES2_SCHEMA, "cim_schema_import_test.v2.json", "0791d733d383ddce6384dcb22ac90839e1b6ac0aed8d1288fab116c1102d0b01")
}

func TestSchemaImportCGMES3(t *testing.T) {
	testSchemaImport(t, CGMES3, CGMES3_SCHEMA, "cim_schema_import_test.v3.json", "243295371e73bb7489d4f7b18967a1ba27a437d3332865d3901b7340ad590366")
}

func testSchemaImport(t *testing.T, cgmesVersion, schemaPattern, output, expectedHash string) {
	t.Helper()
	t.Logf("Start CIM schema import test for %s", cgmesVersion)

	t.Log("Write imported schema to file:", output)
	f, err := os.Create(output)
	if err != nil {
		t.Fatalf("Cannot create output file: %v", err)
	}
	defer f.Close()

	cimSpec := NewCIMSpecification()
	if err := cimSpec.ImportCIMSchemaFiles(schemaPattern); err != nil {
		t.Fatalf("ImportCIMSchemaFiles failed: %v", err)
	}

	if err := cimSpec.printSpecification(f); err != nil {
		t.Fatalf("printSpecification failed: %v", err)
	}

	// Compute hash of the output file for verification
	f.Sync()
	data, err := os.ReadFile(output)
	if err != nil {
		t.Fatalf("Cannot read output file for hashing: %v", err)
	}
	hash := sha256.Sum256(data)
	t.Logf("SHA256 hash of output file: %x", hash)

	// Test output file against expected hash
	if fmt.Sprintf("%x", hash) != expectedHash {
		t.Error("CIM schema import test failed, output file hash does not match expected hash")
	}
}
