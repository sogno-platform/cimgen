package cimgen

import (
	"bytes"
	"log"
	"os"
	"path/filepath"
	"testing"
)

func TestDecodeEncodeCIMData(t *testing.T) {
	t.Log("Start CIM-Data decoding test")

	entries, err := filepath.Glob("test/test_001.xml")
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

		//t.Log("Decoded CIM data:", cimData)

		// Encode back to XML for testing
		f, err := os.Create(entry + ".out.xml")
		if err != nil {
			panic(err)
		}
		defer f.Close()

		EncodeProfile(f, cimData)
	}
}
