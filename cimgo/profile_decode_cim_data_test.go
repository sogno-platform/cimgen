package cimgo

import (
	"bytes"
	"encoding/json"
	"log"
	"os"
	"path/filepath"
	"testing"
)

func TestDecodeCIMData(t *testing.T) {
	t.Log("Start CIM-Data decoding test")

	entries, err := filepath.Glob("../test/test_001.xml")
	if err != nil {
		log.Fatal(err)
	}
	t.Log("Read files:", entries)

	for _, entry := range entries {

		b, err := os.ReadFile(entry)
		if err != nil {
			panic(err)
		}

		cimData, err := DecodeProfile(bytes.NewReader(b))
		if err != nil {
			panic(err)
		}

		jsonOut, err := json.MarshalIndent(cimData.Elements, "", "  ")
		if err != nil {
			t.Fatalf("Failed to create a nicely formatted JSON: %v", err)
		}
		t.Log("Decoded CIM data:\n" + string(jsonOut))
	}
}
