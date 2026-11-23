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
	CGMES2_SCHEMA = "../cgmes-application-profiles-library/CGMES/PastReleases/v2-4/Original/RDFS/*.rdf"
	CGMES3_SCHEMA = "../cgmes-application-profiles-library/CGMES/CurrentRelease/RDFS/*.rdf"
)

func TestDecodeCGMES2(t *testing.T) {
	testDecode(t, CGMES2, CGMES2_SCHEMA, "decoder_test.v2.json", "603dc0d16c18cc02766483b2ff03adcab1b7a1474817ebf1c8611adc03b127c3")
}

func TestDecodeCGMES3(t *testing.T) {
	testDecode(t, CGMES3, CGMES3_SCHEMA, "decoder_test.v3.json", "c734b501e58c89f25816e10666e11edae066c2beb21895ac1c3a3f04078939ff")
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
