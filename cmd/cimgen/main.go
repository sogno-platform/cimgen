package main

import (
	"flag"
	"fmt"
	"log"
	"os"

	"github.com/sogno-platform/cimgen"
)

func main() {
	var schemaPattern string
	var outputDir string
	var language string
	var cgmesVersion string
	var verbose bool

	flag.StringVar(&schemaPattern, "schema", "cgmes_schema/CGMES_3.0.0/IEC61970-600-2_CGMES_3_0_0_RDFS2020_*.rdf", "glob pattern for CIM schema files")
	flag.StringVar(&language, "lang", "go", "output language (e.g., go, python)")
	flag.StringVar(&cgmesVersion, "version", "3.0.0", "CGMES version")
	flag.BoolVar(&verbose, "v", false, "verbose logging")
	flag.Parse()

	logger := log.New(os.Stderr, "", 0)
	if verbose {
		logger.Printf("schema: %s", schemaPattern)
		logger.Printf("output: %s", outputDir)
	}

	// create and populate specification
	cimSpec := cimgen.NewCIMSpecification()
	cimSpec.CGMESVersion = cgmesVersion
	cimSpec.ImportCIMSchemaFiles(schemaPattern)

	switch language {
	case "go":
		// generate Go structs
		gengo := cimgen.NewCIMGeneratorGo(cimSpec)
		outputDir = "cimgostructs"
		gengo.GenerateAllGo(outputDir)
	case "python":
		// generate Python classes
		genpy := cimgen.NewCIMGeneratorPython(cimSpec)
		outputDir = "output/python/v3"
		genpy.GenerateAllPython(outputDir)
	default:
		logger.Fatalf("unsupported language: %s", language)
	}

	logger.Println("done")
	fmt.Println("generated files in:", outputDir)
}
