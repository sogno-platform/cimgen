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

	// deprecated shema files included in the repo
	//schemaFiles := "cgmes_schema/CGMES_3.0.0/IEC61970-600-2_CGMES_3_0_0_RDFS2020_EQ.rdf"
	schemaFiles := "cgmes-application-profiles-library/CGMES/CurrentRelease/RDFS/61970-600-2_*-AP-Voc-RDFS2020.rdf"
	entries, err := filepath.Glob(schemaFiles)
	if err != nil {
		log.Fatal(err)
	}
	t.Log("Read schema files:", entries)

	output := "decoder_test.json"
	t.Log("Write map to file:", output)
	f, err := os.Create(output)
	if err != nil {
		t.Error("failed to open file:", err)
	}
	defer f.Close()

	if _, err := f.Write([]byte("[\n")); err != nil {
		t.Error("failed to write to file:", err)
	}

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

		// add comma and newline for array formatting except for the last entry
		data := append(jsonb, []byte(",\n")...)
		if entry == entries[len(entries)-1] {
			data = append(jsonb, []byte("\n")...)
		}
		if _, err := f.Write([]byte(data)); err != nil {
			t.Error("failed to write to file:", err)
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
		// cut off file path to only file name for easier reading
		filename := filepath.Base(entry)
		t.Logf("hash of profile %x read from file %s", hash, filename)

		// Test output file against expected hash
		if entry == "cgmes-application-profiles-library/CGMES/CurrentRelease/RDFS/61970-600-2_Equipment-AP-Voc-RDFS2020.rdf" {
			expectedHash := "926e6de9bf58f0dce904570557bc7fe5d374e63107929d8d23aa2b84c759983e"
			if fmt.Sprintf("%x", hash) != expectedHash {
				t.Error("decoder tests failed, output file hash does not match expected hash")
			}
		}
	}

	if _, err := f.Write([]byte("]\n")); err != nil {
		t.Error("failed to write to file:", err)
	}
}
