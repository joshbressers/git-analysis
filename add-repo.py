#!/usr/bin/env python3

import sys
import os
import requests
from elasticsearch import Elasticsearch

def main():

    if 'ESURL' not in os.environ:
        es_url = "http://localhost:9200"
    else:
        es_url = os.environ['ESURL']

    es = Elasticsearch([es_url])

    name = sys.argv[1]

    response = requests.get("https://api.github.com/repos/%s" % name)
    repo = response.json()

    if 'message' in repo:
        sys.exit("Repo not found")

    es.update(id=name, index='repos', body={'doc' :repo, 'doc_as_upsert': True}, request_timeout=30)

if __name__ == "__main__":
    main()
