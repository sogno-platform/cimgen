package cimgen

import (
	"bytes"
	"os"
	"path/filepath"
	"strings"
	"text/template"

	"golang.org/x/text/cases"
	"golang.org/x/text/language"
)

func capitalFirstLetter(s string) string {
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

func (spec *CIMSpecification) GenerateGo(outputDir string) {
	// create output folder if it does not exist
	if _, err := os.Stat(outputDir); os.IsNotExist(err) {
		err = os.MkdirAll(outputDir, 0755)
		if err != nil {
			panic(err)
		}
	}

	generateFiles("go_struct", ".go", outputDir, spec.Types)
	generateFile("go_struct_lists", "go_struct_lists.go", outputDir, spec)
	generateFiles("go_enum", ".go", outputDir, spec.Enums)
	generateFiles("go_type_alias", ".go", outputDir, spec.CIMDatatypes)
}

func (spec *CIMSpecification) GeneratePython(outputDir string) {
	// create output folder if it does not exist
	if _, err := os.Stat(outputDir); os.IsNotExist(err) {
		err = os.MkdirAll(outputDir, 0755)
		if err != nil {
			panic(err)
		}
	}

	generateFiles("python_class", ".py", outputDir, spec.Types)
	generateFile("python_constants", "cim_constants.py", outputDir, spec)
	generateFile("python_profile", "cim_profiles.py", outputDir, spec)
	generateFiles("python_datatype", ".py", outputDir, spec.CIMDatatypes)
	generateFiles("python_enum", ".py", outputDir, spec.Enums)
	generateFiles("python_primitive", ".py", outputDir, spec.PrimitiveTypes)
}

// wrapAndIndent is a custom template function that indents a multi-line string.
// It also wraps lines to a maximum of 120 characters.
func wrapAndIndent(spaces int, input string) string {
	// Limit line length to 120 characters
	var resultLines []string
	for len(input) > 120 {
		splitIndex := strings.LastIndex(input[:120], " ")
		if splitIndex == -1 {
			splitIndex = 120
		}
		resultLines = append(resultLines, input[:splitIndex])
		input = input[splitIndex+1:]
	}
	resultLines = append(resultLines, input)
	input = strings.Join(resultLines, "\n")

	// Create the indentation string (e.g., "  " for 2 spaces)
	pad := strings.Repeat(" ", spaces)
	// Split the input into lines
	lines := strings.Split(input, "\n")
	// Buffer to build the output string
	var buf bytes.Buffer

	for i, line := range lines {
		if i > 0 {
			// Add newline before every line except the first
			buf.WriteRune('\n')
		}
		if line != "" {
			// Add the indentation to non-empty lines
			buf.WriteString(pad)
			buf.WriteString(line)
		}
	}
	return buf.String()
}

func (spec *CIMSpecification) GeneratePythonSimple(outputDir string) {
	// create output folder if it does not exist
	if _, err := os.Stat(outputDir); os.IsNotExist(err) {
		err = os.MkdirAll(outputDir, 0755)
		if err != nil {
			panic(err)
		}
	}

	generateFiles("python_simple_class", ".py", outputDir, spec.Types)
	generateFile("python_constants", "CimConstants.py", outputDir, spec)
	generateFile("python_simple_profiles", "CGMESProfile.py", outputDir, spec)
}

func (spec *CIMSpecification) GenerateProto(outputDir string) {
	// create output folder if it does not exist
	if _, err := os.Stat(outputDir); os.IsNotExist(err) {
		err = os.MkdirAll(outputDir, 0755)
		if err != nil {
			panic(err)
		}
	}

	generateFiles("proto_struct", ".proto", outputDir, spec.Types)
}

func (spec *CIMSpecification) GenerateJava(outputDir string) {
	// create output folder if it does not exist
	if _, err := os.Stat(outputDir); os.IsNotExist(err) {
		err = os.MkdirAll(outputDir, 0755)
		if err != nil {
			panic(err)
		}
	}

	enumOuputDir := outputDir + "/types"
	// create output folder for enums if it does not exist
	if _, err := os.Stat(enumOuputDir); os.IsNotExist(err) {
		err = os.MkdirAll(enumOuputDir, 0755)
		if err != nil {
			panic(err)
		}
	}

	spec.setLangTypesJava()

	generateFiles("java_class", ".java", outputDir, spec.Types)
	generateFiles("java_enum", ".java", enumOuputDir, spec.Enums)
	generateFile("java_constants", "CimConstants.java", outputDir, spec)
	generateFile("java_classlist", "CimClassMap.java", outputDir, spec)
	generateFile("java_profile", "CGMESProfile.java", outputDir, spec)
}

func (spec *CIMSpecification) GenerateCpp(outputDir string) {
	// create output folder if it does not exist
	if _, err := os.Stat(outputDir); os.IsNotExist(err) {
		err = os.MkdirAll(outputDir, 0755)
		if err != nil {
			panic(err)
		}
	}

	spec.setLangTypesCpp()
	spec.setDefaultValuesCpp()

	generateFiles("cpp_header", ".hpp", outputDir, spec.Types)
	generateFiles("cpp_object", ".cpp", outputDir, spec.Types)
	generateFiles("cpp_enum_header", ".hpp", outputDir, spec.Enums)
	generateFiles("cpp_enum_object", ".cpp", outputDir, spec.Enums)
	generateFile("cpp_constants_header", "CimConstants.hpp", outputDir, spec)
	generateFile("cpp_constants_object", "CimConstants.cpp", outputDir, spec)
	generateFile("cpp_classlist", "CIMClassList.hpp", outputDir, spec)
	generateFile("cpp_profile_header", "CGMESProfile.hpp", outputDir, spec)
	generateFile("cpp_profile_object", "CGMESProfile.cpp", outputDir, spec)
	generateFile("cpp_iec61970", "IEC61970.hpp", outputDir, spec)
	for _, dt := range spec.CIMDatatypes {
		generateFile("cpp_float_header", dt.Id+".hpp", outputDir, dt)
		generateFile("cpp_float_object", dt.Id+".cpp", outputDir, dt)
	}
	for _, pt := range spec.PrimitiveTypes {
		if pt.Id == "Float" {
			generateFile("cpp_float_header", pt.Id+".hpp", outputDir, pt)
			generateFile("cpp_float_object", pt.Id+".cpp", outputDir, pt)
		} else if pt.Id != "Boolean" && pt.Id != "Integer" {
			generateFile("cpp_string_header", pt.Id+".hpp", outputDir, pt)
			generateFile("cpp_string_object", pt.Id+".cpp", outputDir, pt)
		}
	}
}

func (spec *CIMSpecification) GenerateJS(outputDir string) {
	// create output folder if it does not exist
	if _, err := os.Stat(outputDir); os.IsNotExist(err) {
		err = os.MkdirAll(outputDir, 0755)
		if err != nil {
			panic(err)
		}
	}

	// TODO spec.setLangTypesJS()

	generateFiles("js_class", ".js", outputDir, spec.Types)
	generateFile("js_constants", "CimConstants.js", outputDir, spec)
	generateFile("js_baseclass", "BaseClass.js", outputDir, spec)
	generateFile("js_profile", "CGMESProfile.js", outputDir, spec)
}

func generateFile[T any](tmplFile string, outputFile string, outputDir string, input T) {
	funcMap := template.FuncMap{
		"wrapAndIndent":      wrapAndIndent,
		"capitalFirstLetter": capitalFirstLetter,
		"lower":              Lower,
		"mapDataTypeGo":      MapDataTypeGo,
	}

	// Since ParseFile does not work well with files in subdirectories, we read the file manually
	data, err := os.ReadFile("lang-templates/" + tmplFile + ".tmpl")
	if err != nil {
		panic(err)
	}
	tmpl, err := template.New(tmplFile).Funcs(funcMap).Parse(string(data))
	if err != nil {
		panic(err)
	}

	f, err := os.Create(filepath.Join(outputDir, outputFile))
	if err != nil {
		panic(err)
	}
	defer f.Close()

	err = tmpl.Execute(f, input)
	if err != nil {
		panic(err)
	}
}

func generateFiles[T any](tmplFile string, fileExt string, outputDir string, input map[string]T) {
	funcMap := template.FuncMap{
		"wrapAndIndent":      wrapAndIndent,
		"capitalFirstLetter": capitalFirstLetter,
		"lower":              Lower,
		"mapDataTypeGo":      MapDataTypeGo,
		"joinAttributes":     joinAttributes,
	}

	// Since ParseFile does not work well with files in subdirectories, we read the file manually
	data, err := os.ReadFile("lang-templates/" + tmplFile + ".tmpl")
	if err != nil {
		panic(err)
	}
	tmpl, err := template.New(tmplFile).Funcs(funcMap).Parse(string(data))
	if err != nil {
		panic(err)
	}

	for k, v := range input {
		f, err := os.Create(filepath.Join(outputDir, k+fileExt))
		if err != nil {
			panic(err)
		}
		defer f.Close()

		err = tmpl.Execute(f, v)
		if err != nil {
			panic(err)
		}
	}
}

func joinAttributes(attributes []*CIMAttribute) string {
	filtered := make([]string, 0)
	for _, attr := range attributes {
		if attr.IsClass {
			filtered = append(filtered, attr.Label+"(nullptr)")
		}
	}
	return strings.Join(filtered, ",")
}
