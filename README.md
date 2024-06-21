# <img src="documentation/images/cimgen_logo.png" alt="CIMgen" width=120 />

Python tool for code generation from CIM data model for several programming languages

## Concept overview

![Overview CIMgen](documentation/images/CIMgen.svg)

## Usage example

### Generating C++ files

#### Generating C++ files on Linux

```bash
pip install -e .
cimgen --outdir=output/cpp/CGMES_2.4.15_27JAN2020 --schemadir=cgmes_schema/CGMES_2.4.15_27JAN2020 --langdir=cpp
```

This will build version `CGMES_2.4.15_27JAN2020` in the subfolder `CGMES_2.4.15_27JAN2020_cpp`.

If you wish to build an alternative version, you can see available options in the subfolder called `cgmes_schema`.

#### Generating C++ files in a Docker container

```bash
docker build --tag cimgen --file Dockerfile .
docker run --volume "$(pwd)/output:/output" cimgen --outdir=/output/cpp/CGMES_2.4.15_27JAN2020 --schemadir=/cimgen/cgmes_schema/CGMES_2.4.15_27JAN2020 --langdir=cpp
```

### Generating Python files

#### Generating Python files on Linux

```bash
pip install -e .
cimgen --outdir=output/python/CGMES_2.4.15_27JAN2020 --schemadir=cgmes_schema/CGMES_2.4.15_27JAN2020 --langdir=python
```

`outdir` can be set to whichever absolute path you wish to create the files in.

#### Generating Python files in a Docker container

```bash
docker build --tag cimgen --file Dockerfile .
docker run --volume "$(pwd)/output:/output" cimgen --outdir=/output/python/CGMES_2.4.15_27JAN2020 --schemadir=/cimgen/cgmes_schema/CGMES_2.4.15_27JAN2020 --langdir=python
```

## License

This project is released under the terms of the [Apache 2.0 license](./LICENSE).

## Publications

If you are using CIMgen for your research, please cite the following paper in
your publications:

Dinkelbach, J., Razik, L., Mirz, M., Benigni, A., Monti, A.: Template-based
generation of programming language specific code for smart grid modelling
compliant with CIM and CGMES.
J. Eng. 2023, 1–13 (2022). [https://doi.org/10.1049/tje2.12208](https://doi.org/10.1049/tje2.12208)
