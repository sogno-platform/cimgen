package main

import (
	"github.com/sogno-platform/cimgen"
)

func main() {

	cimSpec := cimgen.NewCIMSpecification()
	cimSpec.ImportCIMSchemaFiles("cgmes_schema/CGMES_3.0.0/IEC61970-600-2_CGMES_3_0_0_RDFS2020_*.rdf")

	gengo := cimgen.NewCIMGeneratorGo(cimSpec)
	outputDir := "cimgo-structs"
	gengo.GenerateAllGo(outputDir)
}
