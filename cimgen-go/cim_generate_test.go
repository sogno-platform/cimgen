// SPDX-FileCopyrightText: 2025 SOGNO
//
// SPDX-License-Identifier: Apache-2.0

package cimgen

import (
	"log"
	"testing"

	"golang.org/x/mod/sumdb/dirhash"
)

func TestGenerate(t *testing.T) {
	t.Log("Start CIM code generation test")

	cimSpec := NewCIMSpecification()
	err := cimSpec.ImportCIMSchemaFiles(CGMES3_SCHEMA)
	if err != nil {
		t.Fatalf("ImportCIMSchemaFiles failed: %v", err)
	}

	outputDir := "output/_go_test"
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
	expectedHash := "h1:wdhFThzdSGD+2QBDxz82ESE9PcdVKdC7RgeDHHToCnk="
	if hash != expectedHash {
		t.Error("CIM code generation test failed, output file hash does not match expected hash")
	}
}
