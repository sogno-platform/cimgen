// SPDX-FileCopyrightText: 2025 SOGNO
//
// SPDX-License-Identifier: Apache-2.0

package cimgen

import (
	"fmt"
	"path/filepath"
	"regexp"
	"strings"
)

var versionNumberRegex = regexp.MustCompile(`\d+[._]\d+[._]\d+`)

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

	// Copy all hardcoded files
	languagesDir, err := findLanguagesDir()
	if err != nil {
		return err
	}
	sourceDir := filepath.Join(languagesDir, "modernpython", "utils")
	if err := copyFilesWithPattern(sourceDir, utilsOutputDir, "*.[mp]*"); err != nil {
		return err
	}

	spec.setLangTypesPython()
	spec.setDefaultValuesPython()
	spec.addNoqaToEnumValueComments()

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
	match := versionNumberRegex.FindString(spec.CGMESVersion)
	if match == "" {
		return fmt.Errorf("cannot parse %s to extract a number", spec.CGMESVersion)
	}
	versionNumber := strings.ReplaceAll(match, "_", ".")
	if err := generateFile("python_init", "__init__.py", resourcesOutputDir, versionNumber); err != nil {
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
	if err := generateFiles("python_simple_datatype", ".py", outputDir, spec.CIMDatatypes); err != nil {
		return err
	}
	if err := generateFiles("python_simple_enum", ".py", outputDir, spec.Enums); err != nil {
		return err
	}
	primitiveTypes := make(map[string]*CIMPrimitive, len(spec.PrimitiveTypes))
	for k, t := range spec.PrimitiveTypes {
		if t.Id != "String" {
			primitiveTypes[k] = t
		}
	}
	if err := generateFiles("python_simple_primitive", ".py", outputDir, primitiveTypes); err != nil {
		return err
	}
	if err := generateFile("python_simple_constants", "CimConstants.py", outputDir, spec); err != nil {
		return err
	}
	if err := generateFile("python_simple_baseclass", "Base.py", outputDir, spec); err != nil {
		return err
	}
	if err := generateFile("python_simple_profiles", "CGMESProfile.py", outputDir, spec); err != nil {
		return err
	}
	if err := generateFile("python_simple_init", "__init__.py", outputDir, spec); err != nil {
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
			setDefaultValuePython(attr)
		}
	}
	for _, t := range cimSpec.CIMDatatypes {
		for _, attr := range t.Attributes {
			setDefaultValuePython(attr)
		}
	}
}

func setDefaultValuePython(attr *CIMAttribute) {
	if attr.IsList || attr.IsClass || attr.IsEnumValue {
		attr.DefaultValue = "None"
	} else {
		attr.DefaultValue = MapDefaultValuePython(attr.DataType)
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

func (cimSpec *CIMSpecification) addNoqaToEnumValueComments() {
	for _, t := range cimSpec.Enums {
		for _, val := range t.Values {
			if val.Comment != "" {
				switch val.Label {
				case "cosPhi", "lPerl", "gPerg", "sPers", "HzPerHz", "VPerV", "APerA", "WPerW":
					val.Comment += "  # noqa: E501, RUF003"
				case "l", "I":
					val.Comment += "  # noqa: E501, E741"
				case "count":
					val.Comment += "  # noqa: E501  # type: ignore"
				default:
					val.Comment += "  # noqa: E501"
				}
			}
		}
	}
}
