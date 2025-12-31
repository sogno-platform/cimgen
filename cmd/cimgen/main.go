package main

import (
	"flag"
	"fmt"
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

	if err := run(logger, schemaPattern, language, cgmesVersion); err != nil {
		logger.Fatalf("Error: %v", err)
	}
}

func run(logger *log.Logger, schemaPattern, language, cgmesVersion string) error {
	logger.Println("Generate code for", language, "from schema files matching", schemaPattern)

	// create and populate specification
	cimSpec := cimgen.NewCIMSpecification()
	cimSpec.CGMESVersion = cgmesVersion
	if err := cimSpec.ImportCIMSchemaFiles(schemaPattern); err != nil {
		return fmt.Errorf("failed to import CIM schema files: %w", err)
	}

	outputVersionDir := ""
	switch cgmesVersion {
	case CGMES3:
		outputVersionDir = "/v3"
	case CGMES2:
		outputVersionDir = "/v2"
	}

	var outputDir string
	switch language {
	case "go":
		// generate Go structs
		outputDir = "output/go" + outputVersionDir
		if err := cimSpec.GenerateGo(outputDir); err != nil {
			return fmt.Errorf("failed to generate Go code: %w", err)
		}
	case "python":
		// generate Python classes
		outputDir = "output/python" + outputVersionDir
		if err := cimSpec.GeneratePython(outputDir); err != nil {
			return fmt.Errorf("failed to generate Python code: %w", err)
		}
	case "python-simple":
		// generate Python simple classes
		outputDir = "output/python-simple" + outputVersionDir
		if err := cimSpec.GeneratePythonSimple(outputDir); err != nil {
			return fmt.Errorf("failed to generate simple Python code: %w", err)
		}
	case "proto":
		// generate Python classes
		outputDir = "output/proto" + outputVersionDir
		if err := cimSpec.GenerateProto(outputDir); err != nil {
			return fmt.Errorf("failed to generate proto code: %w", err)
		}
	case "java":
		// generate Java classes
		outputDir = "output/java" + outputVersionDir
		if err := cimSpec.GenerateJava(outputDir); err != nil {
			return fmt.Errorf("failed to generate Java code: %w", err)
		}
	case "cpp":
		// generate C++ classes
		outputDir = "output/cpp" + outputVersionDir
		if err := cimSpec.GenerateCpp(outputDir); err != nil {
			return fmt.Errorf("failed to generate C++ code: %w", err)
		}
	case "js":
		// generate JavaScript classes
		logger.Println("Javascript generation is experimental")
		outputDir = "output/js" + outputVersionDir
		if err := cimSpec.GenerateJS(outputDir); err != nil {
			return fmt.Errorf("failed to generate JavaScript code: %w", err)
		}
	default:
		return fmt.Errorf("unsupported language: %s", language)
	}

	logger.Println("Generated source files in:", outputDir)
	return nil
}
