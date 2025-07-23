package main

import (
	"bytes"
	"log/slog"
	"os"
	"path/filepath"
	"sort"
	"text/template"
)

func main() {

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

	// create output/golang folder if it does not exist
	outputDir := "output/golang"
	if _, err := os.Stat(outputDir); os.IsNotExist(err) {
		err = os.MkdirAll(outputDir, 0755)
		if err != nil {
			panic(err)
		}
	}

	// loop through all types in the specification and generate a file for each type
	for _, t := range cimSpec.Types {
		var f *os.File
		f, err = os.Create(filepath.Join(outputDir, t.Id+".py"))
		if err != nil {
			panic(err)
		}
		defer f.Close()

		err = tmpl.Execute(f, t)
		if err != nil {
			panic(err)
		}
	}
}
