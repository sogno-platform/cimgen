// SPDX-FileCopyrightText: 2025 SOGNO
//
// SPDX-License-Identifier: Apache-2.0

package cimgen

import (
	"bytes"
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"testing"
)

const (
	CGMES2        = "cgmes_v2_4_15"
	CGMES3        = "cgmes_v3_0_0"
	CGMES2_SCHEMA = "../cgmes-application-profiles-library/CGMES/PastReleases/v2-4/Original/RDFS/*-v2_4_15-4Sep2020.rdf"
	CGMES3_SCHEMA = "../cgmes-application-profiles-library/CGMES/CurrentRelease/RDFS/61970-600-2_*-AP-Voc-RDFS2020.rdf"
)

func TestDecodeCGMES2(t *testing.T) {
	testDecode(t, CGMES2, CGMES2_SCHEMA, "decoder_test.v2.json", "7d2d2f7cf1586b30040b56b1e37665e9e297604ee233cadd95b49c5beedcdcd7")
}

func TestDecodeCGMES3(t *testing.T) {
	testDecode(t, CGMES3, CGMES3_SCHEMA, "decoder_test.v3.json", "eafd799a571073de74f88521341a03bd32b56a753c118356c02ea5411d8d97e2")
}

func testDecode(t *testing.T, cgmesVersion, schemaPattern, output, expectedHash string) {
	t.Helper()
	t.Logf("Start XML decoder test for %s", cgmesVersion)

	entries, err := filepath.Glob(schemaPattern)
	if err != nil {
		t.Fatalf("Glob failed for pattern %s: %v", schemaPattern, err)
	}
	sort.Strings(entries)
	t.Log("Read schema files:\n" + strings.Join(entries, "\n"))

	t.Log("Write map to file:", output)
	f, err := os.Create(output)
	if err != nil {
		t.Fatalf("Cannot create output file: %v", err)
	}
	defer f.Close()

	if _, err := f.Write([]byte("[\n")); err != nil {
		t.Fatalf("failed to write to file: %v", err)
	}

	for i, entry := range entries {

		b, err := os.ReadFile(entry)
		if err != nil {
			t.Fatalf("ReadFile failed for %s: %v", entry, err)
		}

		reader := bytes.NewReader(cleanComments(b))
		resultMap, err := DecodeToMap(reader)
		if err != nil {
			t.Fatalf("DecodeToMap failed for %s: %v", entry, err)
		}

		data, err := json.MarshalIndent(resultMap, "", "  ")
		if err != nil {
			t.Fatalf("MarshalIndent failed for %s: %v", entry, err)
		}

		// add comma and newline for array formatting except for the last entry
		if i < len(entries)-1 {
			data = append(data, ',')
		}
		data = append(data, '\n')

		if _, err := f.Write(data); err != nil {
			t.Fatalf("failed to write to file: %v", err)
		}
	}

	if _, err := f.Write([]byte("]\n")); err != nil {
		t.Fatalf("failed to write to file: %v", err)
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
		t.Errorf("XML decoder test failed for %s, output file hash does not match expected hash", cgmesVersion)
	}
}
