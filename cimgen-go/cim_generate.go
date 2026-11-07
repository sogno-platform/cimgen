package cimgen

import (
	"bytes"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"runtime"
	"sort"
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

func createOutputDir(outputDir string) error {
	if _, err := os.Stat(outputDir); os.IsNotExist(err) {
		if err := os.MkdirAll(outputDir, 0755); err != nil {
			return fmt.Errorf("failed to create output directory %s: %w", outputDir, err)
		}
	}
	return nil
}

// wrapAndIndent is a custom template function that wraps a string to lines with a maximum of characters.
// It is used for comments: make them fit within <width> characters, including indentation.
// The input contains no line breaks and no extra spaces.
func wrapAndIndent(width, indent int, input string) string {
	// Limit line length to width characters
	if indent < 0 {
		indent = 0
	}
	maxLen := width - indent
	if maxLen < 1 {
		maxLen = 1
	}

	runes := []rune(input)
	var resultLines []string
	for len(runes) > maxLen {
		splitIndex := -1
		for i := maxLen; i >= 0; i-- {
			if runes[i] == ' ' {
				splitIndex = i
				break
			}
		}
		if splitIndex == -1 {
			resultLines = append(resultLines, string(runes[:maxLen]))
			runes = runes[maxLen:]
		} else {
			resultLines = append(resultLines, string(runes[:splitIndex]))
			runes = runes[splitIndex+1:]
		}
	}
	resultLines = append(resultLines, string(runes))

	// Create the indentation string (e.g., "  " for 2 spaces)
	pad := strings.Repeat(" ", indent)

	// Buffer to build the output string
	var buf bytes.Buffer
	for i, line := range resultLines {
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

func generateFile[T any](tmplFile string, outputFile string, outputDir string, input T) error {
	funcMap := template.FuncMap{
		"wrapAndIndent":      wrapAndIndent,
		"capitalFirstLetter": capitalFirstLetter,
		"lower":              Lower,
		"add":                func(a, b int) int { return a + b },
		"getPythonTypes": func(cimSpec CIMSpecification) []string {
			allTypes := []string{"Base"}
			for _, t := range cimSpec.Types {
				allTypes = append(allTypes, t.Id)
			}
			for _, t := range cimSpec.Enums {
				allTypes = append(allTypes, t.Id)
			}
			for _, t := range cimSpec.CIMDatatypes {
				allTypes = append(allTypes, t.Id)
			}
			for _, t := range cimSpec.PrimitiveTypes {
				if t.Id != "String" {
					allTypes = append(allTypes, t.Id)
				}
			}
			sort.Strings(allTypes)
			return allTypes
		},
	}

	// Since ParseFile does not work well with files in subdirectories, we read the file manually
	data, err := templatesFS.ReadFile("lang-templates/" + tmplFile + ".tmpl")
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
		"add":                func(a, b int) int { return a + b },
		"startsWith":         strings.HasPrefix,
		"getProtoImports": func(cimType CIMType) []string {
			imports := make(map[string]bool)
			for _, attr := range cimType.Attributes {
				if !(attr.IsPrimitive || attr.IsCIMDatatype) && attr.LangType != "string" {
					imports[attr.DataType] = true
				}
			}
			for _, e := range cimType.EnumTypes {
				imports[e] = true
			}
			result := make([]string, 0, len(imports))
			for k := range imports {
				result = append(result, k)
			}
			sort.Strings(result)
			return result
		},
		"getCppImports": func(cimType CIMType) []string {
			result := make([]string, 0)
			for _, t := range cimType.PrimitiveTypes {
				result = append(result, t)
			}
			for _, t := range cimType.CIMDatatypes {
				result = append(result, t)
			}
			for _, t := range cimType.EnumTypes {
				result = append(result, t)
			}
			sort.Strings(result)
			return result
		},
		"getFixedImports": func(cimType CIMDatatype) []string {
			imports := make(map[string]bool)
			for _, attr := range cimType.Attributes {
				if attr.IsFixed {
					imports[attr.RDFRange] = true
				}
			}
			result := make([]string, 0, len(imports))
			for k := range imports {
				result = append(result, k)
			}
			sort.Strings(result)
			return result
		},
		"collectAttributeTypes": collectAttributeTypes,
	}

	// Since ParseFile does not work well with files in subdirectories, we read the file manually
	data, err := templatesFS.ReadFile("lang-templates/" + tmplFile + ".tmpl")
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

// collectAttributeTypes collects attribute types
// each type is only included once and the list is sorted
func collectAttributeTypes(attributes []*CIMAttribute) []string {
	attributeTypes := make(map[string]bool)
	for _, attr := range attributes {
		if !(attr.IsPrimitive || attr.IsCIMDatatype || attr.IsEnumValue) {
			attributeTypes[attr.DataType] = true
		}
	}
	types := make([]string, 0, len(attributeTypes))
	for k := range attributeTypes {
		types = append(types, k)
	}
	sort.Strings(types)
	return types
}

// cleanAllRecursively removes all files and subdirectories within dir recursively.
func cleanAllRecursively(dir string) error {
	entries, err := os.ReadDir(dir)
	if err != nil {
		if os.IsNotExist(err) {
			return nil
		}
		return err
	}
	for _, entry := range entries {
		if err := os.RemoveAll(filepath.Join(dir, entry.Name())); err != nil {
			return err
		}
	}
	return nil
}

// findLanguagesDir locates the languages directory independently of the working directory.
func findLanguagesDir() (string, error) {
	targetRelPath := filepath.Join("cimgen", "languages")

	// Try relative to this source file
	if _, currentFile, _, ok := runtime.Caller(0); ok {
		candidate := filepath.Clean(filepath.Join(filepath.Dir(currentFile), "..", targetRelPath))
		if info, err := os.Stat(candidate); err == nil && info.IsDir() {
			return candidate, nil
		}
	}

	searchUpwards := func(startDir string) string {
		for dir := startDir; ; {
			candidate := filepath.Join(dir, targetRelPath)
			if info, err := os.Stat(candidate); err == nil && info.IsDir() {
				return candidate
			}
			parent := filepath.Dir(dir)
			if parent == dir {
				break
			}
			dir = parent
		}
		return ""
	}

	// Search upwards from current working directory
	if wd, err := os.Getwd(); err == nil {
		if candidate := searchUpwards(wd); candidate != "" {
			return candidate, nil
		}
	}

	// Search upwards from executable location
	if execPath, err := os.Executable(); err == nil {
		if candidate := searchUpwards(filepath.Dir(execPath)); candidate != "" {
			return candidate, nil
		}
	}

	return "", fmt.Errorf("could not find directory %s", targetRelPath)
}

// copyFilesWithPattern copies all files matching pattern from srcDir to dstDir.
func copyFilesWithPattern(srcDir, dstDir, pattern string) error {
	matches, err := filepath.Glob(filepath.Join(srcDir, pattern))
	if err != nil {
		return err
	}
	for _, file := range matches {
		info, err := os.Stat(file)
		if err != nil {
			return err
		}
		if info.IsDir() {
			continue
		}
		destFile := filepath.Join(dstDir, filepath.Base(file))
		if err := copyFile(file, destFile); err != nil {
			return err
		}
	}
	return nil
}

func copyFile(src, dst string) (err error) {
	in, err := os.Open(src)
	if err != nil {
		return err
	}
	defer in.Close()

	out, err := os.Create(dst)
	if err != nil {
		return err
	}
	defer func() {
		cerr := out.Close()
		if err == nil {
			err = cerr
		}
	}()

	if _, err = io.Copy(out, in); err != nil {
		return err
	}

	info, err := in.Stat()
	if err != nil {
		return err
	}
	return os.Chmod(dst, info.Mode())
}
