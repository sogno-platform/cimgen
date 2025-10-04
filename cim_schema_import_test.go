package cimgen

import (
	"os"
	"path/filepath"
	"sort"
	"testing"
)

func TestSchemaImport(t *testing.T) {
	t.Log("Start CIM schema import test")

	entries, err := filepath.Glob("cgmes_schema/CGMES_3.0.0/IEC61970-600-2_CGMES_3_0_0_RDFS2020_*.rdf")
	if err != nil {
		panic(err)
	}
	sort.Strings(entries)
	t.Log("Read schema from files:", entries)

	output := "cim_schema_import_test.log"
	t.Log("Write imported schema to file:", output)
	f, err := os.Create(output)
	if err != nil {
		t.Error("Cannot create output file:", err)
	}
	defer f.Close()

	cimSpec := NewCIMSpecification()
	cimSpec.ImportCIMSchemaFiles(entries)

	cimSpec.printSpecification(f)

	if cimSpec.Ontologies["DL"].Keyword != "DL" {
		t.Error("cim schema test failed, expected Ontology DL")
	}
}
