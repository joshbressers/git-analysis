#!/usr/bin/env python3

import sys
from git import Repo
from elasticsearch import Elasticsearch

def main():

    es = Elasticsearch(['http://localhost:9200'])

    repo = Repo(sys.argv[1])
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

if __name__ == "__main__":
    main()
