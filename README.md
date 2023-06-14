# dcrx-kv
[![PyPI version](https://img.shields.io/pypi/v/dcrx-kv?color=gre)](https://pypi.org/project/dcrx-kv/)
[![License](https://img.shields.io/github/license/scorbettUM/dcrx-kv)](https://github.com/scorbettUM/dcrx-kv/blob/main/LICENSE)
[![Contributor Covenant](https://img.shields.io/badge/Contributor%20Covenant-2.1-4baaaa.svg)](https://github.com/scorbettUM/dcrx-kv/blob/main/CODE_OF_CONDUCT.md)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/dcrx-kv)](https://pypi.org/project/dcrx-kv/)

DCRX-KV is a RESTful implementation of the dcrx library, allowing you to create Docker images on request! DCRX-KV extends dcrx, providing integrations with the Docker API and dcrx that allow images to be built by making REST requests.

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

DCRX-KV requires a slew of environmental variables in order to run correctly. These include:

```
DCRX_KV_MAX_MEMORY_PERCENT_USAGE=50 # The percent of system memory DCRX-KV and Docker image builds created by DCRX-KV can use. If exceeded, new jobs will be rejected and requests will return a 400 error.

DCRX_KV_JOB_PRUNE_INTERVAL='1s' # How often dcrx-kv checks for done, failed, or cancelled jobs to remove from in-memory storage.

DCRX_KV_JOB_MAX_AGE='1m'= # Time before done, failed, or cancelled jobs are pruned from in-memory storage.

DCRX_KV_JOB_POOL_SIZE=10 # Maximum number of concurrent builds. Default is 10.

DCRX_KV_JOB_WORKERS=4 # Number of workers to use per-job. Default is the number os OS threads.

DCRX_KV_TOKEN_EXPIRATION='15m' # Time for JWT authorization token to expire. Default is 15 minutes.

DCRX_KV_SECRET_KEY=testingthis # Initial secret used to hash user passwords.

DCRX_KV_AUTH_ALGORITHM=HS256 # Algorithm to use for hashing user passwords.

DCRX_KV_DATABASE_TYPE=sqlite # Type of database to use. Default is sqlite and options are mysql, asyncpg, and sqlite.

DCRX_KV_DATABASE_USER=admin # Username used for database connection authentication

DCRX_KV_DATABASE_PASSWORD=test1234 # Password used for database connection authentrication

DCRX_KV_DATABASE_NAME=dcrx # Name of database to use for storing users. Default is dcrx.

DCRX_KV_DATABASE_URI=sqlite+aiosqlite:///dcrx # URL/URI of SQL database for storing users and job metadata.

DCRX_KV_DATABASE_PORT=3369 # Port of SQL database for storing users and job metadata.

DOCKER_REGISTRY_URI=https://docker.io/v1/myrepo/test-images # Default Docker image registry to push images to.

DOCKER_REGISTRY_USERNAME=test # Default Username to authenticate Docker pushes to the provided registry.

DOCKER_REGISTRY_PASSWORD=test-repo-password # Default Password to authenticate Docker pushes to the provided registry.
```

Prior to starting the server, we recommend seeding the database with an initial user. To do so, run the command:

```bash
dcrx-kv database initialize --username $USERNAME --password $PASSWORD --first-name $FIRST_NAME --last-name $LAST_NAME --email $EMAIL
```

If you've chosen to run the Docker image, this step is taken care of for you, with the default user being:

```
username: admin
password: dcrxadmin1*
first-name: admin
last-name: user
email: admin@admin.com
```

Next run:

```bash
dcrx-kv server run
```

and navigate to `localhost:2278/docs`, where you'll find dcrx-kv's OpenAPI documentation.


# Authenticating and Building an Image

From here, we'll need to authenticate using the initial user we created above. Open the tab for `/users/login`, and for the `username` and `password` fields enter the username and password of the initial user, then click `Execute`. A `200` status response containg the initial user's username and id should return.

Next navigate to the `/jobs/images/create` tab. As before, we'll need to fill out some data. Go ahead and copy paste the below into the input for the request body:

```json
{
  "name": "hello-world",
  "tag": "latest",
  "layers": [
    {
      "layer_type": "stage",
      "base": "python",
      "tag": "3.11-slim"
    },
    {
        "layer_type": "entrypoint",
        "command": [
            "echo",
            "Hello world!"
        ]
    }
  ]
}
```

A dcrx-kv image build request requires, at-minimum, a `name`, `tag` and one or more `layer` objects, which will be processed and build in-order of appearance. Note that each layer object almost exactly corresponds to its `dcrx` call. The above corresponds exactly to:

```python

from dcrx import Image

hello_world = Image('hello-world')

hello_world.stage(
    'python',
    '3.11-slim'
).entrypoint([
    'echo',
    'Hello world!'
])
```

Go ahead and submit the request via the `Execute` button. This will start a job to build the specified image and push it to the repository specified in dcrx-kv's environmental variables.

Note that dcrx-kv doesn't wait for the image to be built, instead returning a `JobMetadata` response with a status code of `200`, including the `job_id`. Building images is time-intensive and could potentially bog down a server, so dcrx-kv builds and pushes images in the background. We can use the `job_id` of a Job to make further `GET` requests to the `/jobs/images/{job_id}/get` endpoint to monitor and check how our job is progressing. If we need to cancel a job for any reason, we can simple make a `DELETE` request to `/jobs/images/{job_id}/cancel`.


# Running the Docker Image

To run the Docker image, we recommend first creating a `.env` file with the required environment variables noted above. Then run the image:

```bash
docker run -p 2278:2278 --env-file .env --privileged dcrx-kv:latest
```

# Deploying via Helm

DCRX-KV has a minimal helm chart to help you scale up when ready. To begin, first create a Kuberenetes secret as below:

```
kubectl create secret generic dcrx-kv-secrets --from-literal="DCRX_KV_SECRET_KEY=$DCRX_KV_SECRET_KEY" --from-literal="DOCKER_REGISTRY_USERNAME=$DOCKER_REGISTRY_USERNAME" --from-literal="DOCKER_REGISTRY_PASSWORD=$DOCKER_REGISTRY_PASSWORD"

```

Then install the provided helm chart:

```
helm install dcrx-kv helm/dcrx-kv/ --values helm/dcrx-kv/values.yml
```

The chart creates three replica dcrx-kv pods, a LoadBalancer service, and Nginx ingress to get you up and running in your Kubernetes cluster!


# Notes and Gotchas

1. Does dcrx-kv require a volume to run? - Yes. While dcrx-kv builds images in-memory, Docker still (frustratingly) requires that a physical file be present in the build directory. This means that, if running dcrx-kv in Docker or via Kubernetes, you will need to have a volume with the correct permissions mounted.

2. Does the dcrx-kv Docker image require root? - Currently yes. The dcrx-kv image is based on the latest version of Docker's `dind` image, which runs as and requires root privlidges. We're working on getting the rootless version of `dind` working though!

3. Can I push to a registry besides the default? - Yes. New image job requests can be submitted with optional Registry configuration. For example:

```
{
  "name": "hello-world",
  "tag": "latest",
  "registry": {
    "registry_url": "https://docker.io/v1/mytest/registry",
    "registry_user": "DockerUser100",
    "registry_password": "MyDockerHubToken999*"
  },
  "layers": [
    {
      "layer_type": "stage",
      "base": "python",
      "tag": "3.11-slim"
    },
    {
        "layer_type": "entrypoint",
        "command": [
            "echo",
            "Hello world!"
        ]
    }
  ]
}
```