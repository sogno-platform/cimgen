package cimgen

import (
	"fmt"
	"os"
	"path/filepath"
	"regexp"
	"strings"
)

// GeneratePython generates Python source files from the CIM specification.
func (spec *CIMSpecification) GeneratePython(outputDir string) error {
	if err := cleanAllRecursively(outputDir); err != nil {
		return err
	}

	if err := createOutputDir(outputDir); err != nil {
		return err
	}

	resourcesOutputDir := filepath.Join(outputDir, "resources")
	if err := createOutputDir(resourcesOutputDir); err != nil {
		return err
	}

	utilsOutputDir := filepath.Join(outputDir, "utils")
	if err := createOutputDir(utilsOutputDir); err != nil {
		return err
	}

	spec.setLangTypesPython()
	spec.setDefaultValuesPython()

	if err := generateFiles("python_class", ".py", resourcesOutputDir, spec.Types); err != nil {
		return err
	}
	if err := generateFile("python_constants", "constants.py", utilsOutputDir, spec); err != nil {
		return err
	}
	if err := generateFile("python_profile", "profile.py", utilsOutputDir, spec); err != nil {
		return err
	}
	if err := generateFiles("python_datatype", ".py", resourcesOutputDir, spec.CIMDatatypes); err != nil {
		return err
	}
	if err := generateFiles("python_enum", ".py", resourcesOutputDir, spec.Enums); err != nil {
		return err
	}
	if err := generateFiles("python_primitive", ".py", resourcesOutputDir, spec.PrimitiveTypes); err != nil {
		return err
	}
	if err := writeInitPy(outputDir, spec.CGMESVersion); err != nil {
		return err
	}
	return nil
}

// GeneratePythonSimple generates simple Python source files from the CIM specification.
func (spec *CIMSpecification) GeneratePythonSimple(outputDir string) error {
	if err := cleanAllRecursively(outputDir); err != nil {
		return err
	}

	if err := createOutputDir(outputDir); err != nil {
		return err
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

// setLangTypesPython sets types for attributes based on their data types for Python code generation.
func (cimSpec *CIMSpecification) setLangTypesPython() {
	for _, t := range cimSpec.Types {
		for _, attr := range t.Attributes {
			if attr.IsList {
				attr.LangType = "list"
			} else if attr.IsClass {
				attr.LangType = "Optional[str]"
			} else if attr.IsEnumValue {
				attr.LangType = "str"
			} else {
				attr.LangType = MapDatatypePython(attr.DataType)
			}
		}
	}

	for _, t := range cimSpec.PrimitiveTypes {
		t.LangType = MapDatatypePython(t.Id)
	}

	for _, t := range cimSpec.CIMDatatypes {
		t.LangType = MapDatatypePython(t.PrimitiveType)
	}
}

func MapDatatypePython(t string) string {
	switch t {
	case DataTypeString, DataTypeDateTime, DataTypeDate:
		return "str"
	case DataTypeInteger:
		return "int"
	case DataTypeBoolean:
		return "bool"
	case DataTypeFloat, DateTypeDecimal:
		return "float"
	case DataTypeObject:
		return "Optional[str]"
	default:
		return "str"
	}
}

// setDefaultValuesPython sets default values for attributes based on their data types for Python code generation.
func (cimSpec *CIMSpecification) setDefaultValuesPython() {
	for _, t := range cimSpec.Types {
		for _, attr := range t.Attributes {
			if attr.IsList {
				attr.DefaultValue = "None"
			} else if attr.IsClass {
				attr.DefaultValue = "None"
			} else if attr.IsEnumValue {
				attr.DefaultValue = "None"
			} else {
				attr.DefaultValue = MapDefaultValuePython(attr.DataType)
			}
		}
	}
}

func MapDefaultValuePython(t string) string {
	switch t {
	case DataTypeString, DataTypeDateTime, DataTypeDate, DataTypeMonthDay, DataTypeDuration:
		return "\"\""
	case DataTypeInteger:
		return "0"
	case DataTypeBoolean:
		return "False"
	case DataTypeFloat, DateTypeDecimal:
		return "0.0"
	case DataTypeObject:
		return "None"
	default:
		return "None"
	}
}

var versionNumberRegex = regexp.MustCompile(`\d+_\d+_\d+`)

// writeInitPy writes the package docstring and CGMES_VERSION into resources/__init__.py.
func writeInitPy(outputDir, version string) error {
	match := versionNumberRegex.FindString(version)
	if match == "" {
		return fmt.Errorf("cannot parse %s to extract a number", version)
	}
	versionNumber := strings.ReplaceAll(match, "_", ".")

	dest := filepath.Join(outputDir, "resources", "__init__.py")
	f, err := os.OpenFile(dest, os.O_CREATE|os.O_WRONLY|os.O_APPEND, 0644)
	if err != nil {
		return err
	}
	defer f.Close()

	content := fmt.Sprintf(`"""
Generated from the CGMES files via cimgen: https://github.com/sogno-platform/cimgen
"""

CGMES_VERSION = "%s"
`, versionNumber)

	_, err = f.WriteString(content)
	return err
}
