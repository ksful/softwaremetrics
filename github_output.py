# Helper to enable requests to be run against the GitHub API

import requests, json
from urllib.parse import urlparse
import sys
import configparser

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

def unique(items):
    seen = set([])
    keep = []

    for item in items:
        if item not in seen:
            seen.add(item)
            keep.append(item)

    return keep

config = configparser.ConfigParser()
try:
    config.read('config.ini')
    GITHUB_USER = config['github']['User']
    GITHUB_PASS = config['github']['Password']
    API_URL = config['github']['API']
except:
    eprint("Error reading configuration information.")

def valid_url(url):
    try:
        result = urlparse(url)
        return True if ((result.scheme in set(('http','https'))) and result.netloc) else False
    except:
        return False

#TEST_REPO_URL = 'https://github.com/scipy/scipy'
TEST_REPO_URL = 'https://github.com/codeforscience/sciencefair'


def loadURLs(filename):
    url_list = []
    try:
        with open(filename, 'rb') as f:
            content = f.read().splitlines()
            for line in content:
                string = line.decode('UTF-8')
                if valid_url(string):
                    url_list.append(string)
                else:
                    eprint("Invalid URL detected: ", string)
    except IOError:
        eprint("Error opening: ", filename)
    return url_list


class github_repo(object):
    """ A class to allow manipulation of github urls of different types

    Attributes:
        url: the full original url
        scheme: the scheme e.g. http: https: git:
        owner: the owner of the repository
        reponame: the repository name
    """
    def __init__(self, url):
        o = urlparse(url)
        self.scheme = o.scheme
        self.netloc = o.netloc
        self.params = o.params
        self.query = o.query
        self.fragment = o.fragment
        fullpath = o.path
        self.path = fullpath
        pathparts = fullpath.split('/')
        self.owner = pathparts[1]
        self.reponame = pathparts[2]
        self.queried_watchers = False
        self.queried_stargazers = False
        self.queried_issues = False
#        self.exists = repo_exists(url)

    def repo_exists(repo_url):
        repo = github_repo(repo_url)
        url = API_URL + '/' + 'repos' + '/' + self.owner + '/' + self.reponame + '/' + 'issues' + '?state=all&milestone=*'
        response = requests.get(url, auth=(GITHUB_USER, GITHUB_PASS))
        if response.status_code == 200:
            return True
        else:
            return False

    def query_iterator(self, query_string):
        eprint("Querying ", query_string)
        list_responses = []
        url = API_URL + '/' + 'repos' + '/' + self.owner + '/' + self.reponame + '/' + query_string

        while url:
            response = requests.get(url, auth=(GITHUB_USER, GITHUB_PASS))
            if response.status_code == 200:
                rjson = response.json()
                for item in rjson:
                    list_responses.append(item)
                if 'next' in response.links:
                    url = response.links['next']['url']
                else:
                    url = ''
        return list_responses

    def query_watchers(self):
        self.list_watchers = []
        list_responses = self.query_iterator('subscribers')
        for item in list_responses:
            self.list_watchers.append(item.get('login'))
        self.queried_watchers = True

    def query_stargazers(self):
        self.list_stargazers = []
        list_responses = self.query_iterator('stargazers')
        for item in list_responses:
            self.list_stargazers.append(item.get('login'))
        self.queried_stargazers = True

    def query_issues(self):
        self.list_issues = []
        self.list_prs = []
        ''' This returns both issues and pull requests '''
        self.list_issuesandprs = self.query_iterator('issues?state=all')
        for item in self.list_issuesandprs:
            print(item)
            if item.get('pull_request'):
                self.list_prs.append(item)
            else:
                self.list_issues.append(item)
        self.queried_issues = True

    def num_watchers(self):
        eprint("num_watchers called")
        if not self.queried_watchers:
            self.query_watchers()
        self.num_watchers = len(self.list_watchers)
        return self.num_watchers

    def list_watchers(self):
        eprint("list_watchers called")
        if not self.queried_watchers:
            self.query_watchers()
        return self.list_watchers

    def num_stargazers(self):
        eprint("num_stargazers called")
        if not self.queried_stargazers:
            self.query_stargazers()
        self.num_stargazers = len(self.list_stargazers)
        return self.num_stargazers

    def list_stargazers(self):
        eprint("list_stargazers called")
        if not self.queried_stargazers:
            self.query_stargazers()
        return self.list_stargazers

    def num_issues(self):
        eprint("num_issues called")
        if not self.queried_issues:
            self.query_issues()
        self.num_issues = len(self.list_issues)
        return self.num_issues

    def list_issues(self):
        if not self.queried_issues:
            self.query_issues()
        return self.list_issues

    def num_prs(self):
        eprint("num_prs called")
        if not self.queried_issues:
            self.query_issues()
        self.num_prs = len(self.list_prs)
        return self.num_prs

    def list_prs(self):
        if not self.queried_issues:
            self.query_issues()
        return self.list_prs

    def list_interactors(self):
        ''' I define interactors as everyone who has created an issue
        or commented on an issue.'''
        self.list_interactors = []
        if not self.queried_issues:
            self.query_issues()
        list_issues = self.list_issues
        for issue in list_issues:
            '''Get the name of the creator of the issue'''
            user = issue.get('user')
            interactor = user.get('login')
            self.list_interactors.append(interactor)
            '''Get the names of all commentors'''
            issue_number = issue.get('number')
            list_comments = self.query_iterator('issues/'+str(issue_number)+'/comments')
            for comment in list_comments:
                user = comment.get('user')
                interactor = user.get('login')
                eprint(interactor)
                self.list_interactors.append(interactor)

        return self.list_interactors

    def num_interactors(self):
        ''' The number of unique interactors '''
#        interactors = self.list_interactors()
#        self.num_interactors = unique(interactors)
        return len(self.list_interactors) 



def first_commit(repo_url):
    repo = github_repo(repo_url)
    url = API_URL + '/' + 'repos' + '/' + repo.owner + '/' + repo.reponame + '/' + 'commits'
    response = call_github(url)
    rjson = response.json()
    last_index = len(rjson) - 1
    if last_index >= 0:
        item = rjson[last_index]
        sha = item.get('sha')
        ''' get the date! '''
        commit = item.get('commit')
        author = commit.get('author')
        date = author.get('date')
    else:
        date = None
#    print ("First commit was on: ", date)
#    print ("SHA: ", sha)
    return date

def repo_exists(repo_url):
    repo = github_repo(repo_url)
    url = API_URL + '/' + 'repos' + '/' + repo.owner + '/' + repo.reponame + '/' + 'issues' + '?state=all&milestone=*'
    response = call_github(url)
    if response.status_code == 200:
        return True
    else:
        return False

'''
repos = loadURLs("test.dat")

t = 0
for url in repos:
    print (t, url)
    t = t+1
'''

''' For each repo url, give me the date of the first commit, number of stars, number of contributors
'''
'''
output = open ("python_sample.csv", 'w')
for repo_url in repos:
    ticker = 0;
    if repo_exists(repo_url):
        print ("processing: ", repo_url)
        first_commit_date = first_commit(repo_url)
        stargazers = num_stargazers(repo_url)
        watchers = num_watchers(repo_url)
        output.write(github_repo(repo_url).reponame + ", " + github_repo(repo_url).owner + ", " + str(watchers) + ", " + str(stargazers) + ", " + str(first_commit_date))
        output.write("\n")
        ticker = ticker + 1
        if ticker >= 5:
            output.flush()
            ticker = 0
            print ("FLUSHING\n\n")
output.close()
'''


repo = github_repo(TEST_REPO_URL)
#print ('Number of watchers: ', repo.num_watchers())
print ('List of interactors: ', repo.list_interactors())
print ('Number of unique interactors: ', repo.num_interactors())
#print ('Number of issues: ', repo.num_issues())
#print ('Number of prs: ', repo.num_prs())

#print ('Number of watchers: ', repo.num_watchers())
#print ('List of watchers: ', repo.list_watchers)
#print ('Number of stargazers: ', repo.num_stargazers())
#print ('List of stargazers: ', repo.list_stargazers)


'''issues = num_issues(TEST_REPO_URL)
print ('Number of issues: ', issues)
'''
'''
interactors = list_interactors(TEST_REPO_URL)
print ('List of interactors: ', interactors)
'''
