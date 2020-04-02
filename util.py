import praw
import os.path
import json
import xml.etree.ElementTree as ET
from log import *
from pushshift import *

class Posts:
    postsfile = 'posts.json'
    procpfile = 'processedposts.txt'
    def __init__(self):
        if not os.path.isfile(self.postsfile):
            self.index()
        else:
            self.posts = json.load(open(self.postsfile, 'r'))
        if os.path.isfile(self.procpfile):
            f = open(self.procpfile, 'r')
            procpstr = f.read()
            procpstr.strip()
            self.procp = procpstr.split(',')
            self.procp.remove('')
            f.close()
        else:
            self.procp = []
        
    def processposts(self, posts, method):
        for subm in posts:
            if subm.id not in self.procp and subm.is_self:
                log("Processing post " + subm.id + ' ' + subm.shortlink)            
                method(subm)
                self.procp.append(subm.id)
    def writefiles(self):
        json.dump(self.posts, open(self.postsfile, 'w'))
        with open(self.procpfile, 'w') as f:
            for id in self.procp:
                f.write(id + ',')
    def index(self):
        logp('Started indexing')
        start = int(datetime(2018, 1, 1).timestamp())
        (postsjson, start) = getPushshiftData(sub= 'darkjokes', after= start)
        self.posts = postsjson['data']
        logp('Pushshift search: ' + str(start) + ' ' + 'totalposts: ' + str(len(self.posts)))
        while start is not None:
            (postsjson, start) = getPushshiftData(sub= 'darkjokes', after= start)
            if start is not None:
                self.posts.extend(postsjson['data'])
                logp('Pushshift search: ' + str(start) + ' ' + 'totalposts: ' + str(len(self.posts)))
        logp('Finished querrying for posts')
        json.dump(self.posts, open('posts.json', 'w'))
        # submlist = getPosts(self.posts)
        # logp('Finished getting posts')
        # logp('Started indexing posts')
        # for sub in submlist:
        #     subm = reddit.submission(id= sub)
        #     indexpost(subm)
        logp('Finished indexing posts')