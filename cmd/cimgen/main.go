package main

import (
	"flag"
	"log"
	"os"

	"github.com/sogno-platform/cimgen"
)

const (
	CGMES2        = "2.4.15"
	CGMES3        = "3.0.0"
	CGMES2_SCHEMA = "cgmes_schema/CGMES_2.4.15_27JAN2020/*-v2_4_15-27Jan2020.rdf"
	CGMES3_SCHEMA = "cgmes-application-profiles-library/CGMES/CurrentRelease/RDFS/61970-600-2_*-AP-Voc-RDFS2020.rdf"
)

func main() {
	var schemaPattern string
	var outputDir string
	var language string
	var cgmesVersion string
	var verbose bool

	flag.StringVar(&schemaPattern, "schema", CGMES3_SCHEMA, "glob pattern for CIM schema files")
	flag.StringVar(&language, "lang", "go", "output language (go, python, python-simple, java, proto, cpp, js)")
	flag.StringVar(&cgmesVersion, "version", CGMES3, "CGMES version")
	flag.BoolVar(&verbose, "v", false, "verbose logging")
	flag.Parse()

	logger := log.New(os.Stderr, "", 0)
	if verbose {
		logger.Printf("schema: %s", schemaPattern)
		logger.Printf("language: %s", language)
		logger.Printf("version: %s", cgmesVersion)
	}

	logger.Println("Generate code for", language, "from schema files matching", schemaPattern)

	// create and populate specification
	cimSpec := cimgen.NewCIMSpecification()
	cimSpec.CGMESVersion = cgmesVersion
	cimSpec.ImportCIMSchemaFiles(schemaPattern)

	outputVersionDir := ""
	switch cgmesVersion {
	case CGMES3:
		outputVersionDir = "/v3"
	case CGMES2:
		outputVersionDir = "/v2"
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
		// generate Python simple classes
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
	case "cpp":
		// generate C++ classes
		outputDir = "output/cpp" + outputVersionDir
		cimSpec.GenerateCpp(outputDir)
	case "js":
		// generate JavaScript classes
		logger.Println("Javascript generation is experimental")
		outputDir = "output/js" + outputVersionDir
		cimSpec.GenerateJS(outputDir)
	default:
		logger.Fatalf("unsupported language: %s", language)
	}

	logger.Println("Generated source files in:", outputDir)
}
