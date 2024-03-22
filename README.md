# <img src="documentation/images/cimgen_logo.png" alt="CIMgen" width=120 />

Python tool for code generation from CIM data model for several programming languages

## Concept overview

![Overview CIMgen](documentation/images/CIMgen.svg)

## Usage example

### Generating C++ files

#### Generating C++ files on Linux (Ubuntu)

```bash
sudo apt install python
curl -sSL https://install.python-poetry.org | python3 -  # install poetry
poetry install --no-root # install dependencies
poetry run python ./build.py --outdir=CGMES_2.4.15_27JAN2020_cpp --schemadir=cgmes_schema/CGMES_2.4.15_27JAN2020 --langdir=cpp
```

This will build version CGMES_2.4.15_27JAN2020 in the subfolder CGMES_2.4.15_27JAN2020_cpp.

If you wish to build an alternative version, you can see available options in the subfolder called cgmes_schema.

#### Generating C++ files in a Docker container

```bash
docker build -t cimgen -f Dockerfile .
docker run -v $(pwd)/CGMES_2.4.15_27JAN2020_cpp:/cimgen/cgmes_output cimgen --schemadir=cgmes_schema/CGMES_2.4.15_27JAN2020 --langdir=cpp
```

### Generating Python files

#### Generating Python files on Linux

```bash
sudo apt install python
curl -sSL https://install.python-poetry.org | python3 -  # install poetry
poetry install --no-root # install dependencies
poetry run python ./build.py --outdir=CGMES_2.4.15_27JAN2020_python --schemadir=cgmes_schema/CGMES_2.4.15_27JAN2020 --langdir=python
```

`outdir` can be set to whichever absolute path you wish to create the files in.

#### Generating Python files in a Docker container

```bash
docker build -t cimgen -f Dockerfile .
docker run -v $(pwd)/CGMES_2.4.15_27JAN2020_python:/cimgen/cgmes_output cimgen --schemadir=cgmes_schema/CGMES_2.4.15_27JAN2020 --langdir=python
```

## Publications

If you are using CIMgen for your research, please cite the following paper in
your publications:

Dinkelbach, J., Razik, L., Mirz, M., Benigni, A., Monti, A.: Template-based
generation of programming language specific code for smart grid modelling
compliant with CIM and CGMES.
J. Eng. 2023, 1–13 (2022). [https://doi.org/10.1049/tje2.12208](https://doi.org/10.1049/tje2.12208)
