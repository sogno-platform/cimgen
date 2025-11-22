package cimgen

import (
	"os"
	"path/filepath"
	"text/template"

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
	tmplTypeAlias *template.Template
	tmplEnum      *template.Template
	tmplConstants *template.Template
	tmplProfiles  *template.Template
	tmplDatatype  *template.Template
	tmplPrimitive *template.Template
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

	data, err = os.ReadFile("lang-templates/python_constants.tmpl")
	if err != nil {
		panic(err)
	}
	tmplConstants, err := template.New("python_constants").Parse(string(data))
	if err != nil {
		panic(err)
	}

	data, err = os.ReadFile("lang-templates/python_profile.tmpl")
	if err != nil {
		panic(err)
	}
	tmplProfiles, err := template.New("python_profile").Parse(string(data))
	if err != nil {
		panic(err)
	}

	data, err = os.ReadFile("lang-templates/python_datatype.tmpl")
	if err != nil {
		panic(err)
	}
	tmplDatatype, err := template.New("python_datatype").Parse(string(data))
	if err != nil {
		panic(err)
	}

	data, err = os.ReadFile("lang-templates/python_enum.tmpl")
	if err != nil {
		panic(err)
	}
	tmplEnum, err := template.New("python_enum").Parse(string(data))
	if err != nil {
		panic(err)
	}

	data, err = os.ReadFile("lang-templates/python_primitive.tmpl")
	if err != nil {
		panic(err)
	}
	tmplPrimitive, err := template.New("python_primitive").Parse(string(data))
	if err != nil {
		panic(err)
	}

	return &CIMGenerator{
		cimSpec:       spec,
		tmplType:      tmplType,
		tmplConstants: tmplConstants,
		tmplProfiles:  tmplProfiles,
		tmplDatatype:  tmplDatatype,
		tmplEnum:      tmplEnum,
		tmplPrimitive: tmplPrimitive,
	}
}

func (gen *CIMGenerator) GenerateAllPython(outputDir string) {
	// create output folder if it does not exist
	if _, err := os.Stat(outputDir); os.IsNotExist(err) {
		err = os.MkdirAll(outputDir, 0755)
		if err != nil {
			panic(err)
		}
	}

	for typeName := range gen.cimSpec.Types {
		f, err := os.Create(filepath.Join(outputDir, typeName+".py"))
		if err != nil {
			panic(err)
		}
		defer f.Close()

		err = gen.tmplType.Execute(f, gen.cimSpec.Types[typeName])
		if err != nil {
			panic(err)
		}
	}

	// generate constants file
	f, err := os.Create(filepath.Join(outputDir, "cim_constants.py"))
	if err != nil {
		panic(err)
	}
	defer f.Close()

	err = gen.tmplConstants.Execute(f, gen.cimSpec)
	if err != nil {
		panic(err)
	}

	// generate profiles file
	f, err = os.Create(filepath.Join(outputDir, "cim_profiles.py"))
	if err != nil {
		panic(err)
	}
	defer f.Close()

	err = gen.tmplProfiles.Execute(f, gen.cimSpec)
	if err != nil {
		panic(err)
	}

	// generate datatypes
	for typeName := range gen.cimSpec.CIMDatatypes {
		f, err = os.Create(filepath.Join(outputDir, typeName+".py"))
		if err != nil {
			panic(err)
		}
		defer f.Close()

		err = gen.tmplDatatype.Execute(f, gen.cimSpec.CIMDatatypes[typeName])
		if err != nil {
			panic(err)
		}
	}

	// generate enums
	for typeName := range gen.cimSpec.Enums {
		f, err := os.Create(filepath.Join(outputDir, typeName+".py"))
		if err != nil {
			panic(err)
		}
		defer f.Close()

		err = gen.tmplEnum.Execute(f, gen.cimSpec.Enums[typeName])
		if err != nil {
			panic(err)
		}
	}

	// generate primitives
	for typeName := range gen.cimSpec.PrimitiveTypes {
		f, err := os.Create(filepath.Join(outputDir, typeName+".py"))
		if err != nil {
			panic(err)
		}
		defer f.Close()

		err = gen.tmplPrimitive.Execute(f, gen.cimSpec.PrimitiveTypes[typeName])
		if err != nil {
			panic(err)
		}
	}
}
