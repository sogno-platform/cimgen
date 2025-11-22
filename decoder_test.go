package cimgen

import (
	"bytes"
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"testing"
)

func TestDecode(t *testing.T) {
	t.Log("Start XML decoder test")

	entries, err := filepath.Glob("cgmes_schema/CGMES_3.0.0/IEC61970-600-2_CGMES_3_0_0_RDFS2020_EQ.rdf")
	if err != nil {
		log.Fatal(err)
	}
	t.Log("Read files:", entries)

	for _, entry := range entries {

		b, err := os.ReadFile(entry)
		if err != nil {
			panic(err)
		}

		newMap, err := DecodeToMap(bytes.NewReader(b))
		if err != nil {
			panic(err)
		}

		jsonb, err := json.MarshalIndent(newMap, "", "  ")
		if err != nil {
			panic(err)
		}

		output := "decoder_test.log"
		t.Log("Write map to file:", output)
		err = os.WriteFile(output, jsonb, 0644)
		if err != nil {
			panic(err)
		}

		rdf, ok := newMap["rdf:RDF"]
		if !ok {
			t.Error("decoder tests failed, expected map with key rdf:RDF")
		}

		rdfMap, ok := rdf.(map[string]interface{})
		if !ok {
			t.Error("decoder tests failed, expected map of interface")
		}

		desc, ok := rdfMap["rdf:Description"]
		if !ok {
			t.Error("decoder tests failed, expected map of interface")
		}

		_, ok = desc.([]map[string]interface{})
		if !ok {
			t.Error("decoder tests failed, expected array of map")
		}

		// Compute hash of the output file for verification
		hash := sha256.Sum256(jsonb)
		t.Logf("SHA256 hash of output file: %x", hash)

		// Test output file against expected hash
		expectedHash := "2ca0a11b0ccc3827c93150bc8e6998b54622fdd3bd0a1a1cbf156fbf2e09cdcc" // SHA256 of empty file
		if fmt.Sprintf("%x", hash) != expectedHash {
			t.Error("decoder tests failed, output file hash does not match expected hash")
		}
	}
}
