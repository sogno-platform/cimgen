# Overview of projects based on CIMgen

| Project                 | cpp      | java     | javascript | modernpython | python    |
|:------------------------|:--------:|:--------:|:----------:|:------------:|:---------:|
| sogno-platform          | [libcimpp](https://github.com/sogno-platform/libcimpp) | [c4j](https://github.com/sogno-platform/cim4j) | [pintura](https://github.com/sogno-platform/pintura) | - | [cimpy](https://github.com/sogno-platform/cimpy) |
| Other github            |          |          |            | [alliander-opensource/pycgmes](https://github.com/alliander-opensource/pycgmes) | |
| Release packages        | deb, rpm | -        | docker     | pip          | pip       |
| Current release         | [GitHub](https://github.com/sogno-platform/libcimpp/releases/latest) | - | [Docker Hub](https://hub.docker.com/r/sogno/pintura) | [PyPI](https://pypi.org/project/pycgmes) | [PyPI](https://pypi.org/project/cimpy) |
| **Workflows**           |          |          |            |              |           |
| CIMgen upgrade workflow | -        | -        | -          | -            | -         |
| Check workflow          | -                                                                                       | - | -                                                                                   | [build](https://github.com/alliander-opensource/pycgmes/actions/workflows/build.yaml)   | [pre-commit](https://github.com/sogno-platform/cimpy/actions/workflows/pre-commit.yaml) |
| Build workflow          | [build-src](https://github.com/sogno-platform/libcimpp/actions/workflows/build-src.yml) | - | -                                                                                   | [build](https://github.com/alliander-opensource/pycgmes/actions/workflows/build.yaml)   | [test](https://github.com/sogno-platform/cimpy/actions/workflows/test.yaml)             |
| Test workflow           | -                                                                                       | - | -                                                                                   | [build](https://github.com/alliander-opensource/pycgmes/actions/workflows/build.yaml)   | [test](https://github.com/sogno-platform/cimpy/actions/workflows/test.yaml)             |
| Docs workflow           | [build-doc](https://github.com/sogno-platform/libcimpp/actions/workflows/build-doc.yml) | - | [pages](https://github.com/sogno-platform/pintura/actions/workflows/pages.yaml)     | -                                                                                       | [docs](https://github.com/sogno-platform/cimpy/actions/workflows/docs.yaml)             |
| Release workflow        | [release](https://github.com/sogno-platform/libcimpp/actions/workflows/release.yml)     | - | [release](https://github.com/sogno-platform/pintura/actions/workflows/release.yaml) | [deploy](https://github.com/alliander-opensource/pycgmes/actions/workflows/deploy.yaml) | - |
| **CIM features**        |          |          |            |              |           |
| Multi version           | x        | -        | -          | -            | -         |
| CGMES_2.4.13_18DEC2013  | (source) | -        | -          | -            | -         |
| CGMES_2.4.15_16FEB2016  | (source) | -        | -          | -            | -         |
| CGMES_2.4.15_27JAN2020  | x        | (source) | x          | -            | x         |
| CGMES_3.0.0             | x        | -        | -          | x            | -         |
| Profiles                | x        | -        | x          | x            | -         |
| Custom profiles         | -        | -        | -          | x            | -         |
| Custom namespaces       | -        | -        | -          | x            | -         |
