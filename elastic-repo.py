#!/usr/bin/env python3

import sys
import shutil
import tempfile
from git import Repo
import elasticsearch
import elasticsearch.helpers
from elasticsearch import Elasticsearch

es = Elasticsearch(['http://localhost:9200'])

def main():

    for i in get_repos():
        print("Loading %s" % i)
        load_repo(i)

def load_repo(repo_url):

    repodir = tempfile.mkdtemp()
    repo = Repo.clone_from(repo_url, repodir)
    if repo.bare:
        sys.exit(1, "Repo is a bear")

    url = None
    for i in repo.remotes:
        if i.name == "origin":
            url = i.url

    if url is None:
        sys.exit(1, "No origin URL found")

    for i in repo.iter_commits('master'):
        repo_data = {}
        repo_data['url'] = url
        repo_data['author_email'] = i.author.email
        repo_data['author_tz_offset'] = i.author_tz_offset
        repo_data['authored_date'] = i.authored_date
        repo_data['id'] = i.hexsha
        repo_data['committed_date'] = i.committed_date
        repo_data['committer_email'] = i.committer.email
        repo_data['committer_tz_offset'] = i.committer_tz_offset
        repo_data['conf_encoding'] = i.conf_encoding
        repo_data['env_author_date'] = i.env_author_date
        repo_data['env_committer_date'] = i.env_committer_date
        if i.gpgsig:
            repo_data['gpgsig'] = True
        else:
            repo_data['gpgsig'] = False
        repo_data['message'] = i.message
        repo_data['size'] = i.size

        try:
            es.update(id=repo_data['id'], index="git", doc_type='doc', body={'doc' :repo_data, 'doc_as_upsert': True})
        except:
            print("Exception")
            print(repo_data)
            print("--------------------------")

    shutil.rmtree(repodir)

def get_repos():

    repos = []

    query = { "_source": ["clone_url"],
              "query" : {
                "match_all" : {}
              }
            }

    es_data = elasticsearch.helpers.scan(es, index="repos", query=query, scroll='5m')

    for i in es_data:
        repos.append(i['_source']['clone_url'])

    return repos

if __name__ == "__main__":
    main()
