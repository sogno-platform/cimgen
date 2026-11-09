package main

import (
	"flag"
	"fmt"
	"log"
	"os"

	"github.com/sogno-platform/cimgen"
)

const (
	CGMES2        = "cgmes_v2_4_15"
	CGMES3        = "cgmes_v3_0_0"
	CGMES2_SCHEMA = "../cgmes-application-profiles-library/CGMES/PastReleases/v2-4/Original/RDFS/*-v2_4_15-4Sep2020.rdf"
	CGMES3_SCHEMA = "../cgmes-application-profiles-library/CGMES/CurrentRelease/RDFS/61970-600-2_*-AP-Voc-RDFS2020.rdf"
)

func main() {
	var schemaPattern string
	var language string
	var cgmesVersion string
	var verbose bool
	var outputDir string

	flag.StringVar(&language, "lang", "", "output language (required: go, python, python-simple, java, proto, cpp, js)")
	flag.StringVar(&cgmesVersion, "version", CGMES3, "CGMES version ("+CGMES2+", "+CGMES3+")")
	flag.StringVar(&schemaPattern, "schema", "", "glob pattern for CIM schema files")
	flag.StringVar(&outputDir, "output", "", "output directory")
	flag.BoolVar(&verbose, "v", false, "verbose logging")
	flag.BoolVar(&verbose, "verbose", false, "verbose logging")
	flag.Parse()

	logger := log.New(os.Stderr, "", 0)

	if language == "" {
		logger.Println("Error: -lang is required")
		flag.Usage()
		os.Exit(1)
	}

	if cgmesVersion != CGMES2 && cgmesVersion != CGMES3 {
		logger.Println("Error: -version must be", CGMES2, "or", CGMES3)
		flag.Usage()
		os.Exit(1)
	}

	// Set default schema pattern for cgmes_v2_4_15 and cgmes_v3_0_0
	if schemaPattern == "" {
		if cgmesVersion == CGMES2 {
			schemaPattern = CGMES2_SCHEMA
		} else if cgmesVersion == CGMES3 {
			schemaPattern = CGMES3_SCHEMA
		}
	}

	// Set default output directory for cgmes_v2_4_15 and cgmes_v3_0_0
	if outputDir == "" {
		outputDir = "output/" + language
		if cgmesVersion == CGMES2 {
			outputDir += "/v2"
		} else if cgmesVersion == CGMES3 {
			outputDir += "/v3"
		}
	}

	if verbose {
		logger.Printf("language  : %s", language)
		logger.Printf("version   : %s", cgmesVersion)
		logger.Printf("schema    : %s", schemaPattern)
		logger.Printf("output    : %s", outputDir)
	}

	if err := run(logger, schemaPattern, language, cgmesVersion, outputDir); err != nil {
		logger.Fatalf("Error: %v", err)
	}
}

func run(logger *log.Logger, schemaPattern, language, cgmesVersion string, outputDir string) error {
	logger.Println("Generate code for", language, "from schema files matching", schemaPattern)

	// create and populate specification
	cimSpec := cimgen.NewCIMSpecification()
	cimSpec.CGMESVersion = cgmesVersion
	if err := cimSpec.ImportCIMSchemaFiles(schemaPattern); err != nil {
		return fmt.Errorf("failed to import CIM schema files: %w", err)
	}

	type generatorFunc func(spec *cimgen.CIMSpecification, outputDir string) error

	generators := map[string]generatorFunc{
		"go":            (*cimgen.CIMSpecification).GenerateGo,
		"python":        (*cimgen.CIMSpecification).GeneratePython,
		"python-simple": (*cimgen.CIMSpecification).GeneratePythonSimple,
		"proto":         (*cimgen.CIMSpecification).GenerateProto,
		"java":          (*cimgen.CIMSpecification).GenerateJava,
		"cpp":           (*cimgen.CIMSpecification).GenerateCpp,
		"js": func(spec *cimgen.CIMSpecification, outputDir string) error {
			logger.Println("Javascript generation is experimental")
			return spec.GenerateJavaScript(outputDir)
		},
	}

	generator, ok := generators[language]
	if !ok {
		return fmt.Errorf("unsupported language: %s", language)
	}

	if err := generator(cimSpec, outputDir); err != nil {
		return fmt.Errorf("failed to generate %s code: %w", language, err)
	}

	logger.Println("Generated source files in:", outputDir)
	return nil
}
