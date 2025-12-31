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

func createOutputDir(outputDir string) error {
	if _, err := os.Stat(outputDir); os.IsNotExist(err) {
		if err := os.MkdirAll(outputDir, 0755); err != nil {
			return fmt.Errorf("failed to create output directory %s: %w", outputDir, err)
		}
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

func generateFile[T any](tmplFile string, outputFile string, outputDir string, input T) error {
	funcMap := template.FuncMap{
		"wrapAndIndent":      wrapAndIndent,
		"capitalFirstLetter": capitalFirstLetter,
		"lower":              Lower,
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
