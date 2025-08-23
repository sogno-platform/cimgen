package main

import (
	"bytes"
	"fmt"
	"log/slog"
	"os"
	"path/filepath"
	"sort"
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
	sort.Strings(entries)
	fmt.Println("Read schema from files:", entries)

	output := "cim_schema_test.log"
	fmt.Println("Write imported schema to file:", output)
	f, err := os.Create(output)
	if err != nil {
		slog.Any("error", err)
	}
	defer f.Close()

	cimSpec := newCIMSpecification()

	for _, entry := range entries {
		b, err := os.ReadFile(entry)
		if err != nil {
			panic(err)
		}

		resultMap, err := DecodeToMap(bytes.NewReader(b))
		if err != nil {
			panic(err)
		}

		cimSpec.addRDFMap(resultMap)
	}

	cimSpec.postprocess()

	cimSpec.printSpecification(f)

	if cimSpec.Ontologies["DL"].Keyword != "DL" {
		t.Error("cim schema test failed, expected Ontology DL")
	}
}
