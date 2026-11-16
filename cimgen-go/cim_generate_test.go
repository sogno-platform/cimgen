// SPDX-FileCopyrightText: 2025 SOGNO
//
// SPDX-License-Identifier: Apache-2.0

package cimgen

import (
	"log"
	"testing"

	"golang.org/x/mod/sumdb/dirhash"
)

func TestGenerateCGMES2(t *testing.T) {
	testGenerate(t, CGMES2, CGMES2_SCHEMA, "output/_go_test.v2", "h1:/etA1UZYr6yj4Dep0haZVQNPlrgQc8Te/pMPn6cC3OM=")
}

func TestGenerateCGMES3(t *testing.T) {
	testGenerate(t, CGMES3, CGMES3_SCHEMA, "output/_go_test.v3", "h1:zS6SMZEQwwiPrKzGzXgHVxcdh5yVOITa/4p0FJyaN9s=")
}

func testGenerate(t *testing.T, cgmesVersion, schemaPattern, outputDir, expectedHash string) {
	t.Logf("Start CIM code generation test for %s", cgmesVersion)

	cimSpec := NewCIMSpecification(cgmesVersion)
	err := cimSpec.ImportCIMSchemaFiles(schemaPattern)
	if err != nil {
		t.Fatalf("ImportCIMSchemaFiles failed: %v", err)
	}

	err = cimSpec.GenerateGo(outputDir)
	if err != nil {
		t.Fatalf("GenerateGo failed: %v", err)
	}

	hash, err := dirhash.HashDir(outputDir, "", dirhash.Hash1)
	if err != nil {
		log.Fatal(err)
	}
	t.Logf("Directory Hash: %s", hash)

	// Test directory hash
	if hash != expectedHash {
		t.Error("CIM code generation test failed, output file hash does not match expected hash")
	}
}
