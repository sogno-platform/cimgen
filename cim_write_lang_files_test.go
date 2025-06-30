package cimgen

import (
	"bytes"
	"log/slog"
	"os"
	"path/filepath"
	"sort"
	"testing"
	"text/template"
)

func TestGenerate(t *testing.T) {

	var logLevel = new(slog.LevelVar)
	logLevel.Set(slog.LevelInfo)
	slog.SetDefault(slog.New(slog.NewTextHandler(os.Stderr, &slog.HandlerOptions{Level: logLevel})))

	entries, err := filepath.Glob("cgmes_schema/CGMES_3.0.0/IEC61970-600-2_CGMES_3_0_0_RDFS2020_*.rdf")
	if err != nil {
		panic(err)
	}
	sort.Strings(entries)

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

	var tmplFile = "cimpy_class_template.tmpl"
	tmpl, err := template.New(tmplFile).ParseFiles(tmplFile)
	if err != nil {
		panic(err)
	}

	var f *os.File
	f, err = os.Create("cim_write_lang_files_test.py")
	if err != nil {
		panic(err)
	}
	defer f.Close()

	err = tmpl.Execute(f, cimSpec.Types["ACDCTerminal"])
	if err != nil {
		panic(err)
	}
}
