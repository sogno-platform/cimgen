package cimgen

import (
	"bytes"
	"fmt"
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

func (spec *CIMSpecification) GenerateGo(outputDir string) error {
	// create output folder if it does not exist
	if _, err := os.Stat(outputDir); os.IsNotExist(err) {
		err = os.MkdirAll(outputDir, 0755)
		if err != nil {
			return fmt.Errorf("failed to create output directory %s: %w", outputDir, err)
		}
	}

	if err := generateFiles("go_struct", ".go", outputDir, spec.Types); err != nil {
		return err
	}
	if err := generateFile("go_struct_lists", "go_struct_lists.go", outputDir, spec); err != nil {
		return err
	}
	if err := generateFiles("go_enum", ".go", outputDir, spec.Enums); err != nil {
		return err
	}
	if err := generateFiles("go_type_alias", ".go", outputDir, spec.CIMDatatypes); err != nil {
		return err
	}
	return nil
}

func (spec *CIMSpecification) GeneratePython(outputDir string) error {
	// create output folder if it does not exist
	if _, err := os.Stat(outputDir); os.IsNotExist(err) {
		err = os.MkdirAll(outputDir, 0755)
		if err != nil {
			return fmt.Errorf("failed to create output directory %s: %w", outputDir, err)
		}
	}

	spec.setLangTypesPython()
	spec.setDefaultValuesPython()

	if err := generateFiles("python_class", ".py", outputDir, spec.Types); err != nil {
		return err
	}
	if err := generateFile("python_constants", "cim_constants.py", outputDir, spec); err != nil {
		return err
	}
	if err := generateFile("python_profile", "cim_profiles.py", outputDir, spec); err != nil {
		return err
	}
	if err := generateFiles("python_datatype", ".py", outputDir, spec.CIMDatatypes); err != nil {
		return err
	}
	if err := generateFiles("python_enum", ".py", outputDir, spec.Enums); err != nil {
		return err
	}
	if err := generateFiles("python_primitive", ".py", outputDir, spec.PrimitiveTypes); err != nil {
		return err
	}
	return nil
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

func (spec *CIMSpecification) GeneratePythonSimple(outputDir string) error {
	// create output folder if it does not exist
	if _, err := os.Stat(outputDir); os.IsNotExist(err) {
		err = os.MkdirAll(outputDir, 0755)
		if err != nil {
			return fmt.Errorf("failed to create output directory %s: %w", outputDir, err)
		}
	}

	spec.setLangTypesPython()
	spec.setDefaultValuesPython()

	if err := generateFiles("python_simple_class", ".py", outputDir, spec.Types); err != nil {
		return err
	}
	if err := generateFile("python_constants", "CimConstants.py", outputDir, spec); err != nil {
		return err
	}
	if err := generateFile("python_simple_profiles", "CGMESProfile.py", outputDir, spec); err != nil {
		return err
	}
	return nil
}

func (spec *CIMSpecification) GenerateProto(outputDir string) error {
	// create output folder if it does not exist
	if _, err := os.Stat(outputDir); os.IsNotExist(err) {
		err = os.MkdirAll(outputDir, 0755)
		if err != nil {
			return fmt.Errorf("failed to create output directory %s: %w", outputDir, err)
		}
	}

	if err := generateFiles("proto_struct", ".proto", outputDir, spec.Types); err != nil {
		return err
	}
	return nil
}

func (spec *CIMSpecification) GenerateJava(outputDir string) error {
	// create output folder if it does not exist
	if _, err := os.Stat(outputDir); os.IsNotExist(err) {
		err = os.MkdirAll(outputDir, 0755)
		if err != nil {
			return fmt.Errorf("failed to create output directory %s: %w", outputDir, err)
		}
	}

	enumOuputDir := outputDir + "/types"
	// create output folder for enums if it does not exist
	if _, err := os.Stat(enumOuputDir); os.IsNotExist(err) {
		err = os.MkdirAll(enumOuputDir, 0755)
		if err != nil {
			return fmt.Errorf("failed to create output directory %s: %w", enumOuputDir, err)
		}
	}

	spec.setLangTypesJava()

	if err := generateFiles("java_class", ".java", outputDir, spec.Types); err != nil {
		return err
	}
	if err := generateFiles("java_enum", ".java", enumOuputDir, spec.Enums); err != nil {
		return err
	}
	if err := generateFile("java_constants", "CimConstants.java", outputDir, spec); err != nil {
		return err
	}
	if err := generateFile("java_classlist", "CimClassMap.java", outputDir, spec); err != nil {
		return err
	}
	if err := generateFile("java_profile", "CGMESProfile.java", outputDir, spec); err != nil {
		return err
	}
	return nil
}

func (spec *CIMSpecification) GenerateCpp(outputDir string) error {
	// create output folder if it does not exist
	if _, err := os.Stat(outputDir); os.IsNotExist(err) {
		err = os.MkdirAll(outputDir, 0755)
		if err != nil {
			return fmt.Errorf("failed to create output directory %s: %w", outputDir, err)
		}
	}

	spec.setLangTypesCpp()
	spec.setDefaultValuesCpp()

	if err := generateFiles("cpp_header", ".hpp", outputDir, spec.Types); err != nil {
		return err
	}
	if err := generateFiles("cpp_object", ".cpp", outputDir, spec.Types); err != nil {
		return err
	}
	if err := generateFiles("cpp_enum_header", ".hpp", outputDir, spec.Enums); err != nil {
		return err
	}
	if err := generateFiles("cpp_enum_object", ".cpp", outputDir, spec.Enums); err != nil {
		return err
	}
	if err := generateFile("cpp_constants_header", "CimConstants.hpp", outputDir, spec); err != nil {
		return err
	}
	if err := generateFile("cpp_constants_object", "CimConstants.cpp", outputDir, spec); err != nil {
		return err
	}
	if err := generateFile("cpp_classlist", "CIMClassList.hpp", outputDir, spec); err != nil {
		return err
	}
	if err := generateFile("cpp_profile_header", "CGMESProfile.hpp", outputDir, spec); err != nil {
		return err
	}
	if err := generateFile("cpp_profile_object", "CGMESProfile.cpp", outputDir, spec); err != nil {
		return err
	}
	if err := generateFile("cpp_iec61970", "IEC61970.hpp", outputDir, spec); err != nil {
		return err
	}
	for _, dt := range spec.CIMDatatypes {
		if err := generateFile("cpp_float_header", dt.Id+".hpp", outputDir, dt); err != nil {
			return err
		}
		if err := generateFile("cpp_float_object", dt.Id+".cpp", outputDir, dt); err != nil {
			return err
		}
	}
	for _, pt := range spec.PrimitiveTypes {
		if pt.Id == "Float" {
			if err := generateFile("cpp_float_header", pt.Id+".hpp", outputDir, pt); err != nil {
				return err
			}
			if err := generateFile("cpp_float_object", pt.Id+".cpp", outputDir, pt); err != nil {
				return err
			}
		} else if pt.Id != "Boolean" && pt.Id != "Integer" {
			if err := generateFile("cpp_string_header", pt.Id+".hpp", outputDir, pt); err != nil {
				return err
			}
			if err := generateFile("cpp_string_object", pt.Id+".cpp", outputDir, pt); err != nil {
				return err
			}
		}
	}
	return nil
}

func (spec *CIMSpecification) GenerateJS(outputDir string) error {
	// create output folder if it does not exist
	if _, err := os.Stat(outputDir); os.IsNotExist(err) {
		err = os.MkdirAll(outputDir, 0755)
		if err != nil {
			return fmt.Errorf("failed to create output directory %s: %w", outputDir, err)
		}
	}

	// TODO spec.setLangTypesJS()

	if err := generateFiles("js_class", ".js", outputDir, spec.Types); err != nil {
		return err
	}
	if err := generateFile("js_constants", "CimConstants.js", outputDir, spec); err != nil {
		return err
	}
	if err := generateFile("js_baseclass", "BaseClass.js", outputDir, spec); err != nil {
		return err
	}
	if err := generateFile("js_profile", "CGMESProfile.js", outputDir, spec); err != nil {
		return err
	}
	return nil
}

func generateFile[T any](tmplFile string, outputFile string, outputDir string, input T) error {
	funcMap := template.FuncMap{
		"wrapAndIndent":      wrapAndIndent,
		"capitalFirstLetter": capitalFirstLetter,
		"lower":              Lower,
	}

	// Since ParseFile does not work well with files in subdirectories, we read the file manually
	data, err := os.ReadFile("lang-templates/" + tmplFile + ".tmpl")
	if err != nil {
		return fmt.Errorf("failed to read template %s: %w", tmplFile, err)
	}
	tmpl, err := template.New(tmplFile).Funcs(funcMap).Parse(string(data))
	if err != nil {
		return fmt.Errorf("failed to parse template %s: %w", tmplFile, err)
	}

	f, err := os.Create(filepath.Join(outputDir, outputFile))
	if err != nil {
		return fmt.Errorf("failed to create output file %s: %w", outputFile, err)
	}
	defer f.Close()

	err = tmpl.Execute(f, input)
	if err != nil {
		return fmt.Errorf("failed to execute template %s for file %s: %w", tmplFile, outputFile, err)
	}
	return nil
}

func generateFiles[T any](tmplFile string, fileExt string, outputDir string, input map[string]T) error {
	funcMap := template.FuncMap{
		"wrapAndIndent":      wrapAndIndent,
		"capitalFirstLetter": capitalFirstLetter,
		"lower":              Lower,
		"joinAttributesCpp":  joinAttributesCpp,
	}

	// Since ParseFile does not work well with files in subdirectories, we read the file manually
	data, err := os.ReadFile("lang-templates/" + tmplFile + ".tmpl")
	if err != nil {
		return fmt.Errorf("failed to read template %s: %w", tmplFile, err)
	}
	tmpl, err := template.New(tmplFile).Funcs(funcMap).Parse(string(data))
	if err != nil {
		return fmt.Errorf("failed to parse template %s: %w", tmplFile, err)
	}

	for k, v := range input {
		f, err := os.Create(filepath.Join(outputDir, k+fileExt))
		if err != nil {
			return fmt.Errorf("failed to create output file %s: %w", k+fileExt, err)
		}
		defer f.Close()

		err = tmpl.Execute(f, v)
		if err != nil {
			return fmt.Errorf("failed to execute template %s for file %s: %w", tmplFile, k+fileExt, err)
		}
	}
	return nil
}

func joinAttributesCpp(attributes []*CIMAttribute) string {
	filtered := make([]string, 0)
	for _, attr := range attributes {
		if attr.IsClass {
			filtered = append(filtered, attr.Label+"(nullptr)")
		}
	}
	return strings.Join(filtered, ", ")
}
