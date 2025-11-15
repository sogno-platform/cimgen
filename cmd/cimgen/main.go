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
	var verbose bool

	flag.StringVar(&schemaPattern, "schema", "cgmes_schema/CGMES_3.0.0/IEC61970-600-2_CGMES_3_0_0_RDFS2020_*.rdf", "glob pattern for CIM schema files")
	flag.StringVar(&outputDir, "out", "cimgostructs", "output directory")
	flag.BoolVar(&verbose, "v", false, "verbose logging")
	flag.Parse()

	logger := log.New(os.Stderr, "", 0)
	if verbose {
		logger.Printf("schema: %s", schemaPattern)
		logger.Printf("output: %s", outputDir)
	}

	// create and populate specification
	cimSpec := cimgen.NewCIMSpecification()
	cimSpec.ImportCIMSchemaFiles(schemaPattern)

	// generate Go structs
	gengo := cimgen.NewCIMGeneratorGo(cimSpec)
	gengo.GenerateAllGo(outputDir)

	logger.Println("done")
	fmt.Println("generated files in:", outputDir)
}
