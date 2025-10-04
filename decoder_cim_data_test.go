package cimgen

import (
	"bytes"
	"log"
	"os"
	"path/filepath"
	"testing"
)

func TestDecodeCIMData(t *testing.T) {
	t.Log("Start CIM-Data decoding test")

	entries, err := filepath.Glob("ieee-9bus.xml")
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

		t.Log("Decoded CIM data:", cimData)
	}
}
