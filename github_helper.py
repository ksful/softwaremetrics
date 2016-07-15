# Helper to enable requests to be run against the GitHub API

import requests, json
from urllib.parse import urlparse

API_URL = "https://api.github.com"
TEST_REPO_URL = 'https://github.com/softwaresaved/softwaremetrics'

# url = "https://api.github.com/repos/softwaresaved/softwaremetrics/subscribers"

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

    def owner(self):
        return self.owner

    def reponame(self):
        return self.reponame

def call_github(url):
    response = requests.get(url)
    return response

def num_watchers(repo_url):
    repo = github_repo(repo_url)
    #rebuild URL
    url = API_URL + '/' + 'repos' + '/' + repo.owner + '/' + repo.reponame + '/' + 'subscribers'
    response = call_github(url)
    rjson = response.json()
    return len(rjson)


watchers = num_watchers(TEST_REPO_URL)
print ('Watchers: ', watchers)



#print(response)
#print('---')

#rjson = response.json()

#print(rjson)

#parsed_json = json.loads(response)

#for item in rjson:
#    parsed_json = json.load(item)
#    print ('Item ', item)
#    print (item)
#    print ('---')
#    parsed_json = json.dumps(item)
#    for criteria in parsed_json:
#    for key, value in item.items():
#        print (key, 'is: ', value)
#        print ('')

#watchers = len(rjson)
#print ('Number of watchers: ', watchers)
