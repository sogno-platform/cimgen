package cimgen

import (
	"bytes"
	"encoding/json"
	"fmt"
	"log"
	"log/slog"
	"os"
	"path/filepath"
	"testing"
)

func TestDecode(t *testing.T) {

	var logLevel = new(slog.LevelVar)
	logLevel.Set(slog.LevelInfo)
	slog.SetDefault(slog.New(slog.NewTextHandler(os.Stderr, &slog.HandlerOptions{Level: logLevel})))

	entries, err := filepath.Glob("cgmes_schema/CGMES_3.0.0/IEC61970-600-2_CGMES_3_0_0_RDFS2020_TP.rdf")
	if err != nil {
		log.Fatal(err)
	}
	fmt.Println("Read files:", entries)

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
		fmt.Println("Write map to file:", output)
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

		arr, ok := desc.([]map[string]interface{})
		if !ok {
			t.Error("decoder tests failed, expected array of map")
		}

		v, ok := arr[0]["@rdf:about"]
		if !ok {
			t.Error("decoder tests failed, expected key @rdf:about")
		}

		about, ok := v.(string)
		if !ok {
			t.Error("decoder tests failed, expected string")
		}

		if about != "http://iec.ch/TC57/ns/CIM/Topology-EU#Ontology" {
			t.Error("decoder tests failed, expected different string value")
		}
	}
}
