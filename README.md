<!--
SPDX-FileCopyrightText: 2019 SOGNO

SPDX-License-Identifier: Apache-2.0
-->

# CIMgen

CIMgen is a command-line tool that generates language-specific data models (classes, structs) from Common Information Model (CIM) RDF schemas. It is designed to parse complex CIM RDF files and produce idiomatic code in various programming languages like Go, C++, Java, and Python.

Several projects use CIMgen, see [Projects using CIMgen](docs/CIMgenProjects.md).

![Overview CIMgen](docs/images/cimgen_concept.svg)

## CIMgen Go

This is a rewrite of CIMgen in the Go programming language.

### How to Build and Run

Make sure that you have cloned the repo recursively to include the CGMES schema files from ENTSO-E

```bash
git clone --recurse-submodules [...]
```

or clone the submodule in a second step

```bash
git submodule update --init --recursive
```

Ensure that GOPATH is set and included in your PATH.

Change to the `cimgen-go` directory:

```bash
cd cimgen-go
```

Use the `go run` command, specifying the target language with the `--lang` option.

```bash
# Example for generating C++ code
go run cmd/cimgen/main.go --lang cpp
```

Alternatively, you can install cimgen.

```bash
go install ./...
```

### How to Test

Run the test suite using the `go test` command. The `-v` flag provides verbose output.

```bash
go test -v ./...
```

### Debugging

To analyze differences between generated file you can use

```bash
git diff --no-index --word-diff --diff-filter=MR --ignore-space-change --ignore-blank-lines output/[dir 1] output/[dir 2]
diff -wB output/[dir 1] output/[dir 2]
```

### Architecture

The code generation process follows these main steps:

1. **Schema Loading:** The tool begins by finding and parsing the relevant CIM RDF schema files based on the specified version and profiles.
2. **Schema Processing:** It processes the parsed RDF data into an internal, language-agnostic representation of CIM classes, properties, datatypes, and their relationships.
3. **Code Generation:** Using Go's `text/template` engine, it feeds the internal representation into language-specific templates (`lang-templates/*.tmpl`) to generate the final source code files.

### Key Go Files

- `cmd/cimgen/main.go`: The main entry point for the CLI tool. It parses command-line arguments and orchestrates the code generation process.
- `cim_generate.go`: Contains the core logic for driving the generation process for a specific language.
- `cim_schema_import.go`: Handles the discovery and parsing of the CIM RDF schema files.
- `cim_schema_processing.go`: Responsible for transforming the raw parsed schema into the internal representation used by the generators.
- `generator_*.go`: A set of files (e.g., `generator_go.go`, `generator_cpp.go`) that implement the generation logic for each target language.

## CIMgen Python

Python tool for code generation from CIM data model for several programming languages

### Usage

Run the following, replacing `<lang>` with the target language:

```bash
pip install -e .
cimgen --lang <lang>
```

This will build version `cgmes_v3_0_0` in the directory `output/<lang>/v3`.

Supported values for `--lang` (required):

- `cpp`
- `python-simple`
- `python`, i.e. PyDantic based dataclasses
- `js`
- `java`
- `javadb`

Additional options:

- `--version`: CGMES Version
  - `cgmes_v2_4_15`
  - `cgmes_v3_0_0` (default)
- `--schema`: Pattern for CIM schema files (or several patterns, separated by commas)
- `--output`: Output directory
- `--verbose` (flag, default: False)

If options `--schema` or `--output` are not specified,
they are set automatically:

version       | schema                                                                         | output
:------------ | :----------------------------------------------------------------------------- | :-----
cgmes_v2_4_15 | cgmes-application-profiles-library/CGMES/PastReleases/v2-4/Original/RDFS/*.rdf | output/\<lang\>/v2
cgmes_v3_0_0  | cgmes-application-profiles-library/CGMES/CurrentRelease/RDFS/*.rdf             | output/\<lang\>/v3

### Custom Profiles

To generate code for custom profiles, specify one or more file patterns using the `--schema` option. Multiple patterns can be passed as a comma-separated list:

```bash
# Generate code for custom profiles
cimgen --lang <lang> --schema "path/to/custom/*.rdf"

# Combine standard profiles with custom profiles
cimgen --lang <lang> --schema "cgmes-application-profiles-library/CGMES/CurrentRelease/RDFS/*.rdf,path/to/custom/*.rdf"
```

### Development

For the python toolchain, install the package in dev mode:

```bash
pip install -e .[dev]
```

Run pre-commit checks manually:

```bash
pre-commit run --all-files
```

Install pre-commit hook to run it automatically:

```bash
pre-commit install
```

## License

This project is released under the terms of the [Apache 2.0 license](./LICENSE).

## Publications

If you are using CIMgen for your research, please cite the following paper in
your publications:

Dinkelbach, J., Razik, L., Mirz, M., Benigni, A., Monti, A.: Template-based
generation of programming language specific code for smart grid modelling
compliant with CIM and CGMES.
J. Eng. 2023, 1-13 (2022). [https://doi.org/10.1049/tje2.12208](https://doi.org/10.1049/tje2.12208)
