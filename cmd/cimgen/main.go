package main

import (
	"flag"
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

	logger.Println("Generate code for", language, "from schema files matching", schemaPattern)

	// create and populate specification
	cimSpec := cimgen.NewCIMSpecification()
	cimSpec.CGMESVersion = cgmesVersion
	cimSpec.ImportCIMSchemaFiles(schemaPattern)

	outputVersionDir := ""
	switch cgmesVersion {
	case "3.0.0":
		outputVersionDir = "/v3"
	}

	switch language {
	case "go":
		// generate Go structs
		outputDir = "output/go" + outputVersionDir
		cimSpec.GenerateGo(outputDir)
	case "python":
		// generate Python classes
		outputDir = "output/python" + outputVersionDir
		cimSpec.GeneratePython(outputDir)
	case "python-simple":
		// generate Python classes
		outputDir = "output/python-simple" + outputVersionDir
		cimSpec.GeneratePythonSimple(outputDir)
	case "proto":
		// generate Python classes
		outputDir = "output/proto" + outputVersionDir
		cimSpec.GenerateProto(outputDir)
	case "java":
		// generate Java classes
		outputDir = "output/java" + outputVersionDir
		cimSpec.GenerateJava(outputDir)
	default:
		logger.Fatalf("unsupported language: %s", language)
	}

	logger.Println("Generated source files in:", outputDir)
}
