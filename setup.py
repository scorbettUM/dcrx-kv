import os
from setuptools import (
    setup,
    find_packages
)

current_directory = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(current_directory, 'README.md'), "r") as readme:
    package_description = readme.read()

version_string = ""
with open (os.path.join(current_directory, ".version"), 'r') as version_file:
    version_string = version_file.read()

setup(
    name="dcrx-kv",
    version=version_string,
    description="A RESTful implementation of the DCRX Docker library.",
    long_description=package_description,
    long_description_content_type="text/markdown",
    author="Sean Corbett",
    author_email="sean.corbett@umontana.edu",
    url="https://github.com/scorbettUM/dcrx-kv",
    packages=find_packages(),
    keywords=[
        'pypi', 
        'cicd', 
        'python',
        'setup',
        'docker',
        'infra',
        'devops',
        'fastapi',
    ],
    classifiers=[
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent"
    ],

    entry_points = {
        'console_scripts': [
            'dcrx-kv=dcrx_kv.cli:run'
        ],
    },
    install_requires=[
        'dcrx',
        'fastapi[all]',
        'docker',
        'psutil',
        'python-jose[cryptography]',
        'passlib[bcrypt]',
        'python-dotenv',
        'click',
        'uvicorn[standard]'
    ],
    extras_requires={
        'all': [
            'aiomysql',
            'asyncpg',
            'sqlalchemy',
            'aiosqlite',
            'sqlalchemy-utils',
            'psycopg2-binary'
        ],
        's3': [
            'boto3'
        ],
        'gcs': [
            'google-cloud-storage',
        ],
        'azure': [
            'azure-storage-blob'
        ]
    },
    python_requires='>=3.10'
)
