// SPDX-FileCopyrightText: 2025 SOGNO
//
// SPDX-License-Identifier: Apache-2.0

package cimgen

import (
	"crypto/sha256"
	"fmt"
	"os"
	"testing"
)

func TestSchemaImportCGMES2(t *testing.T) {
	testSchemaImport(t, CGMES2, CGMES2_SCHEMA, "cim_schema_import_test.v2.json", "6b58bc77a7474795184f85391fcaa012606192455db87144c84dcda490d16b67")
}

func TestSchemaImportCGMES3(t *testing.T) {
	testSchemaImport(t, CGMES3, CGMES3_SCHEMA, "cim_schema_import_test.v3.json", "1188025d36e22537e16fc2bf2f08502434b5135c718eacbb07c82786488993cb")
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

	cimSpec := NewCIMSpecification(cgmesVersion)
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
