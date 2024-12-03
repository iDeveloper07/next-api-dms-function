#! /bin/bash
cd layers/requests
mkdir -p python/lib/python3.12/site-packages
docker run -v "$PWD":/var/task "public.ecr.aws/sam/build-python3.12:latest" /bin/sh -c "pip install -r requirements.txt -t python/lib/python3.12/site-packages/; exit"
zip -r -o requests.zip python > /dev/null
cd ../../
cd layers/psycopg2
mkdir -p python/lib/python3.12/site-packages
docker run -v "$PWD":/var/task "public.ecr.aws/sam/build-python3.12:latest" /bin/sh -c "pip install -r requirements.txt -t python/lib/python3.12/site-packages/; exit"
zip -r -o psycopg2.zip python > /dev/null
cd ../../
 