package cimgen

import (
	"bytes"
	"encoding/json"
	"fmt"
	"log/slog"
	"os"
	"path/filepath"
	"testing"
)

func TestSchemaImport(t *testing.T) {

	var logLevel = new(slog.LevelVar)
	logLevel.Set(slog.LevelInfo)
	slog.SetDefault(slog.New(slog.NewTextHandler(os.Stderr, &slog.HandlerOptions{Level: logLevel})))

	entries, err := filepath.Glob("cgmes_schema/CGMES_3.0.0/IEC61970-600-2_CGMES_3_0_0_RDFS2020_*.rdf")
	if err != nil {
		panic(err)
	}
	fmt.Println("Read schema from files:", entries)

	output := "cim_schema_test.log"
	fmt.Println("Write imported schema to file:", output)
	f, err := os.Create(output)
	if err != nil {
		slog.Any("error", err)
	}
	defer f.Close()

	allCimTypesMerged := make(map[string]*CIMType, 0)
	allCimEnums := make(map[string]*CIMEnum, 0)
	allCimOntologies := make(map[string]*CIMOntology, 0)

	for _, entry := range entries {
		b, err := os.ReadFile(entry)
		if err != nil {
			panic(err)
		}

		resultMap, err := DecodeToMap(bytes.NewReader(b))
		if err != nil {
			panic(err)
		}

		cimTypes, cimEnums, cimOntologies := processRDFMap(resultMap)

		allCimTypesMerged = mergeCimTypes(allCimTypesMerged, cimTypes)

		for k, v := range cimEnums {
			allCimEnums[k] = v
		}

		for k, v := range cimOntologies {
			allCimOntologies[k] = v
		}
	}

	jsonb, err := json.MarshalIndent(allCimOntologies, "", "  ")
	if err != nil {
		panic(err)
	}
	f.WriteString(string(jsonb) + "\n")

	jsonb, err = json.MarshalIndent(allCimTypesMerged, "", "  ")
	if err != nil {
		panic(err)
	}
	f.WriteString(string(jsonb) + "\n")

	jsonb, err = json.MarshalIndent(allCimEnums, "", "  ")
	if err != nil {
		panic(err)
	}
	f.WriteString(string(jsonb) + "\n")

	if allCimOntologies["DL"].Keyword != "DL" {
		t.Error("cim schema test failed, expected Ontology DL")
	}
}
