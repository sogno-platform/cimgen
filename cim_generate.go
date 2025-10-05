package cimgen

import (
	"html/template"
	"os"
	"path/filepath"

	"golang.org/x/text/cases"
	"golang.org/x/text/language"
)

func CapitalizeFirstLetter(s string) string {
	if len(s) == 0 {
		return s
	}
	return cases.Upper(language.English).String(s[:1]) + s[1:]
}

func Lower(s string) string {
	if len(s) == 0 {
		return s
	}
	return cases.Lower(language.English).String(s)
}

type CIMGenerator struct {
	cimSpec      *CIMSpecification
	tmplType     *template.Template
	tmplTypeList *template.Template
}

func NewCIMGeneratorPython(spec *CIMSpecification) *CIMGenerator {
	// Since ParseFile does not work well with files in subdirectories, we read the file manually
	data, err := os.ReadFile("lang-templates/python_class_template.tmpl")
	if err != nil {
		panic(err)
	}
	tmplType, err := template.New("python_class_template").Parse(string(data))
	if err != nil {
		panic(err)
	}
	return &CIMGenerator{
		cimSpec:  spec,
		tmplType: tmplType,
	}
}

func NewCIMGeneratorGo(spec *CIMSpecification) *CIMGenerator {
	funcMap := template.FuncMap{
		"capitalizefirstletter": CapitalizeFirstLetter,
		"lower":                 Lower,
	}

	// Since ParseFile does not work well with files in subdirectories, we read the file manually
	data, err := os.ReadFile("lang-templates/go_struct_template.tmpl")
	if err != nil {
		panic(err)
	}
	tmplType, err := template.New("go_struct_template").Funcs(funcMap).Parse(string(data))
	if err != nil {
		panic(err)
	}

	data, err = os.ReadFile("lang-templates/go_struct_list_template.tmpl")
	if err != nil {
		panic(err)
	}
	tmplTypeList, err := template.New("go_struct_list_template").Funcs(funcMap).Parse(string(data))
	if err != nil {
		panic(err)
	}

	return &CIMGenerator{
		cimSpec:      spec,
		tmplType:     tmplType,
		tmplTypeList: tmplTypeList,
	}
}

func (gen *CIMGenerator) GenerateType(typeName string, outputFile string) {
	f, err := os.Create(outputFile)
	if err != nil {
		panic(err)
	}
	defer f.Close()

	err = gen.tmplType.Execute(f, gen.cimSpec.Types[typeName])
	if err != nil {
		panic(err)
	}
}

func (gen *CIMGenerator) GenerateAllGo(outputDir string) {
	// create output folder if it does not exist
	if _, err := os.Stat(outputDir); os.IsNotExist(err) {
		err = os.MkdirAll(outputDir, 0755)
		if err != nil {
			panic(err)
		}
	}

	for typeName := range gen.cimSpec.Types {
		f, err := os.Create(filepath.Join(outputDir, typeName+".go"))
		if err != nil {
			panic(err)
		}
		defer f.Close()

		err = gen.tmplType.Execute(f, gen.cimSpec.Types[typeName])
		if err != nil {
			panic(err)
		}
	}

	// generate struct list
	var f *os.File
	f, err := os.Create(filepath.Join(outputDir, "struct_list.go"))
	if err != nil {
		panic(err)
	}
	defer f.Close()

	err = gen.tmplTypeList.Execute(f, gen.cimSpec)
	if err != nil {
		panic(err)
	}
}
