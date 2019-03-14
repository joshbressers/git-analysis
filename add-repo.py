#!/usr/bin/env python3

import sys
import requests
from elasticsearch import Elasticsearch

def main():

    es = Elasticsearch(['http://localhost:9200'])

    name = sys.argv[1]

    response = requests.get("https://api.github.com/repos/%s" % name)
    repo = response.json()

    if 'message' in repo:
        sys.exit("Repo not found")

    es.update(id=name, index='repos', doc_type='_doc', body={'doc' :repo, 'doc_as_upsert': True}, request_timeout=30)

if __name__ == "__main__":
    main()
