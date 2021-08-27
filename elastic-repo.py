#!/usr/bin/env python3

import sys
import os
import json
import shutil
import tempfile
from git import Repo
import elasticsearch
import elasticsearch.helpers
from elasticsearch import Elasticsearch
from tqdm import tqdm

import argparse

parser = argparse.ArgumentParser()

parser.add_argument('--repo', '-r', action="store",
                    dest="repo", help="Specify a path to a repo")
parser.add_argument('--branch', '-b', action="store", default="main",
                    dest="branch", help="Specify the default branch")
args = parser.parse_args()


if 'ESURL' not in os.environ:
    es_url = "http://localhost:9200"
else:
    es_url = os.environ['ESURL']

es = Elasticsearch([es_url])

class Commits:

    def __init__(self):
        self.commits = []

    def add(self, commit_data):

        new_data = {
            '_op_type': 'update',
            '_index': "git",
            '_id': commit_data['id'],
            'doc_as_upsert': True,
            'doc': commit_data
        }

        self.commits.append(new_data)

        return self.__maybe_update__()

    def __maybe_update__(self, force = False):
        # Send updates in batches of 100

        if len(self.commits) < 500 and force != True:
            return

        errors = []

        for ok, item in elasticsearch.helpers.streaming_bulk(es, self.commits, max_retries=2):
            if not ok:
                errors.append(item)

        self.commits = []

        return errors

    def done(self):
        return self.__maybe_update__(True)

def main():

    # First let's see if the index exists
    if es.indices.exists('git') is False:
        # We have to create it and add a mapping
        fh = open('mapping.json')
        mapping = json.load(fh)
        es.indices.create('git', body=mapping)

    if args.repo is None:
        repo_data = get_repos()
        for i in repo_data:
            print("Loading %s" % i)
            tmpdir = clone_repo(i)
            git_repo = open_repo(tmpdir.name)
            load_repo(git_repo, repo_data[i])
            tmpdir.cleanup()
    else:
        git_repo = open_repo(args.repo)
        load_repo(git_repo, args.branch)

def clone_repo(repo_url):
    tmpdir = tempfile.TemporaryDirectory()
    repodir = tmpdir.name
    repo = Repo.clone_from(repo_url, repodir)
    if repo.bare:
        sys.exit(1, "Repo is a bear")
    repo.close()

    return tmpdir

def open_repo(repo_path):
    return Repo(repo_path)

def load_repo(repo, default_branch):

    the_commits = Commits()

    total_commits = sum(1 for _ in repo.iter_commits(default_branch))

    url = None
    for i in repo.remotes:
        if i.name == "origin":
            url = i.url

    if url is None:
        sys.exit(1, "No origin URL found")

    for i in tqdm(repo.iter_commits(default_branch), total=total_commits):
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

        errors = the_commits.add(repo_data)
        if errors:
            print("Bad Things Happened")
            print(errors)
            print("--------------------------")


    errors = the_commits.done()
    if errors:
        print("Bad Things Happened")
        print(errors)
        print("--------------------------")

def get_repos():

    repos = {}

    query = { "_source": ["clone_url", "default_branch"],
              "query" : {
                "match_all" : {}
              }
            }

    es_data = elasticsearch.helpers.scan(es, index="repos", query=query, scroll='5m')

    for i in es_data:
        repos[i['_source']['clone_url']] = i['_source']['default_branch']

    return repos

if __name__ == "__main__":
    main()
