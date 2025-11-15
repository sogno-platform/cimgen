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

func MapDataTypeGo(s string) string {
	if len(s) == 0 {
		return s
	}
	switch s {
	case DataTypeString:
		return "string"
	case DataTypeBoolean:
		return "bool"
	case DataTypeInteger:
		return "int"
	case DataTypeFloat:
		return "float64"
	case DataTypeDateTime:
		return "string" // TODO: time.Time
	default:
		return s // assume it's a struct type
	}
}

type CIMGenerator struct {
	cimSpec       *CIMSpecification
	tmplType      *template.Template
	tmplTypeList  *template.Template
	tmplDataset   *template.Template
	tmplTypeAlias *template.Template
	tmplEnum      *template.Template
}

func NewCIMGeneratorPython(spec *CIMSpecification) *CIMGenerator {
	// Since ParseFile does not work well with files in subdirectories, we read the file manually
	data, err := os.ReadFile("lang-templates/python_class.tmpl")
	if err != nil {
		panic(err)
	}
	tmplType, err := template.New("python_class").Parse(string(data))
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
		"mapDataTypeGo":         MapDataTypeGo,
	}

	// Since ParseFile does not work well with files in subdirectories, we read the file manually
	data, err := os.ReadFile("lang-templates/go_struct.tmpl")
	if err != nil {
		panic(err)
	}
	tmplType, err := template.New("go_struct").Funcs(funcMap).Parse(string(data))
	if err != nil {
		panic(err)
	}

	data, err = os.ReadFile("lang-templates/go_struct_lists.tmpl")
	if err != nil {
		panic(err)
	}
	tmplTypeList, err := template.New("go_struct_lists").Funcs(funcMap).Parse(string(data))
	if err != nil {
		panic(err)
	}

	data, err = os.ReadFile("lang-templates/go_type_alias.tmpl")
	if err != nil {
		panic(err)
	}
	tmplTypeAlias, err := template.New("go_type_alias").Funcs(funcMap).Parse(string(data))
	if err != nil {
		panic(err)
	}

	data, err = os.ReadFile("lang-templates/go_enum.tmpl")
	if err != nil {
		panic(err)
	}
	tmplEnum, err := template.New("go_enum").Funcs(funcMap).Parse(string(data))
	if err != nil {
		panic(err)
	}

	return &CIMGenerator{
		cimSpec:       spec,
		tmplType:      tmplType,
		tmplTypeList:  tmplTypeList,
		tmplTypeAlias: tmplTypeAlias,
		tmplEnum:      tmplEnum,
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

		// generate type alias if needed
		if gen.cimSpec.Types[typeName].Stereotype == "CIMDatatype" {
			err = gen.tmplTypeAlias.Execute(f, gen.cimSpec.Types[typeName])
			if err != nil {
				panic(err)
			}
		} else {
			err = gen.tmplType.Execute(f, gen.cimSpec.Types[typeName])
			if err != nil {
				panic(err)
			}
		}
	}

	// generate CIM struct lists
	f, err := os.Create(filepath.Join(outputDir, "cim_struct_lists.go"))
	if err != nil {
		panic(err)
	}
	defer f.Close()

	err = gen.tmplTypeList.Execute(f, gen.cimSpec)
	if err != nil {
		panic(err)
	}

	// generate enums
	for typeName := range gen.cimSpec.Enums {
		f, err := os.Create(filepath.Join(outputDir, typeName+".go"))
		if err != nil {
			panic(err)
		}
		defer f.Close()

		err = gen.tmplEnum.Execute(f, gen.cimSpec.Enums[typeName])
		if err != nil {
			panic(err)
		}
	}

}
