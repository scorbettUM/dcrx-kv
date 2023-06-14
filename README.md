# dcrx-kv
[![PyPI version](https://img.shields.io/pypi/v/dcrx-kv?color=gre)](https://pypi.org/project/dcrx-kv/)
[![License](https://img.shields.io/github/license/scorbettUM/dcrx-kv)](https://github.com/scorbettUM/dcrx-kv/blob/main/LICENSE)
[![Contributor Covenant](https://img.shields.io/badge/Contributor%20Covenant-2.1-4baaaa.svg)](https://github.com/scorbettUM/dcrx-kv/blob/main/CODE_OF_CONDUCT.md)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/dcrx-kv)](https://pypi.org/project/dcrx-kv/)

DCRX-KV is a RESTful key/value service that utilizes a combination of an in-memory filesystem and permanent storage to facilitate easy upload and download of files. DCRX-KV permanent storage is accomplished via integrations with:

- AWS S3
- Azure Blob Storage
- Google Cloud Storage

and/or writing to disk.

DCRX-KV also includes basic JWT authorization and user management (no-RBAC), and is intended to be deployed as an internal-facing service. dcrx also provides OpenAPI documentation to make getting started intuitive, and features integrations with SQLite, Postgres, and MySQL for storing and managing users.


# Setup and Installation

DCRX-KV is available both as a Docker image and as a PyPi package. For local use, we recommend using PyPi, Python 3.10+, and a virtual environment. To install, run:

```bash
python -m venv ~/.dcrx && \
source ~/.dcrx/bin/activate && \
pip install dcrx-kv
```

To get the Docker image, run:

```
docker pull adalundhe/dcrx-kv:latest
```


# Getting Started

TBA