# Helper to enable requests to be run against the GitHub API

import requests, json
from urllib.parse import urlparse
import sys
import configparser

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

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

TEST_REPO_URL = 'https://github.com/scipy/scipy'

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

    def query_watchers(self):
        eprint("Querying watchers")
        self.list_watchers = []
        url = API_URL + '/' + 'repos' + '/' + self.owner + '/' + self.reponame + '/' + 'subscribers'

        while url:
            response = requests.get(url, auth=(GITHUB_USER, GITHUB_PASS))
            rjson = response.json()
            for item in rjson:
                self.list_watchers.append(item.get('login'))
            if 'next' in response.links:
                url = response.links['next']['url']
            else:
                url = ''
        self.queried_watchers = True

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

    def owner(self):
        return self.owner

    def reponame(self):
        return self.reponame

def call_github(url):
    full_response = []
    while url:
        response = requests.get(url, auth=(GITHUB_USER, GITHUB_PASS))
#        rjson = response.json()
#        print ("=====")
#        print (rjson)
#        full_response.append(json.loads(rjson))
        if 'next' in response.links:
            url = response.links['next']['url']
#            print("URL: ",url)
#            print(full_response)
        else:
            url = ''
#            print("Finished traversing")

    #print (links)
    #print ('Response text: ============================================')
    #print (response.text)
    #return json.dumps(full_response)
    return response

def num_stargazers(repo_url):
    repo = github_repo(repo_url)
    #rebuild URL
    url = API_URL + '/' + 'repos' + '/' + repo.owner + '/' + repo.reponame + '/' + 'stargazers'
    response = call_github(url)
    rjson = response.json()
    return len(rjson)

def num_issues(repo_url):
    repo = github_repo(repo_url)
    url = API_URL + '/' + 'repos' + '/' + repo.owner + '/' + repo.reponame + '/' + 'issues' + '?state=all&milestone=*'
    response = call_github(url)
    rjson = response.json()
    return len(rjson)

def list_interactors(repo_url):
    # I define interactors as everyone who has created an issue or commented on an issue.
    repo = github_repo(repo_url)
    url = API_URL + '/' + 'repos' + '/' + repo.owner + '/' + repo.reponame + '/' + 'issues'
    response = call_github(url)
    rjson = response.json()
    interactors = []
    for item in rjson:
        user = item.get('user')
        interactors.append(user.get('login'))
#        user_list = item.get('user')
#        print('List:', user_list)
#        for user in user_list:
#            print('User: ', user)
#            interactors.append(user.get('login'))
#        assignee_list = item.get('assignee')
#        for assignee in assignee_list:
#            interactors.append(item.get('login'))
    return interactors

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
print ('Number of watchers: ', repo.num_watchers())
print ('List of watchers: ', repo.list_watchers)


'''issues = num_issues(TEST_REPO_URL)
print ('Number of issues: ', issues)
'''
'''
interactors = list_interactors(TEST_REPO_URL)
print ('List of interactors: ', interactors)
'''
