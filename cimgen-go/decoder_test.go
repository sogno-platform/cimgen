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

const (
	CGMES3        = "3.0.0"
	CGMES3_SCHEMA = "../cgmes-application-profiles-library/CGMES/CurrentRelease/RDFS/61970-600-2_*-AP-Voc-RDFS2020.rdf"
)

func TestDecode(t *testing.T) {
	t.Log("Start XML decoder test")

	entries, err := filepath.Glob(CGMES3_SCHEMA)
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
			t.Fatalf("ReadFile failed for %s: %v", entry, err)
		}

		newMap, err := DecodeToMap(bytes.NewReader(b))
		if err != nil {
			t.Fatalf("DecodeToMap failed for %s: %v", entry, err)
		}

		jsonb, err := json.MarshalIndent(newMap, "", "  ")
		if err != nil {
			t.Fatalf("MarshalIndent failed for %s: %v", entry, err)
		}

		// add comma and newline for array formatting except for the last entry
		data := append(jsonb, []byte(",\n")...)
		if entry == entries[len(entries)-1] {
			data = append(jsonb, []byte("\n")...)
		}
		if _, err := f.Write([]byte(data)); err != nil {
			t.Error("failed to write to file:", err)
		}
	}

	if _, err := f.Write([]byte("]\n")); err != nil {
		t.Error("failed to write to file:", err)
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
	expectedHash := "eafd799a571073de74f88521341a03bd32b56a753c118356c02ea5411d8d97e2"
	if fmt.Sprintf("%x", hash) != expectedHash {
		t.Error("decoder tests failed, output file hash does not match expected hash")
	}
}
