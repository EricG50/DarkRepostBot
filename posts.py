import praw
import os.path
import xml.etree.ElementTree as ET
from log import *
from pushshift import *
from util import *

class Posts:
    postsfile = 'posts.xml'
    procpfile = 'processedposts.txt'
    def __init__(self, subreddit):
        if not os.path.isfile(self.postsfile): 
            self.index(subreddit)
        else:
            Posts.postsxml = ET.parse(self.postsfile)
            Posts.posts = Posts.postsxml.getroot()
        if not os.path.isfile(self.procpfile):
            procpstr = ''
        else:
            with open(self.procpfile, 'r') as f:
                procpstr = f.read()
        procpstr.strip()
        self.procp = procpstr.split(',')
        self.procp.remove('')
    def processposts(self, posts, method):
        for subm in posts:
            if subm.id not in self.procp and subm.is_self:
                log("Processing post " + subm.id + ' ' + subm.shortlink)            
                method(subm)
                self.procp.append(subm.id)
    def writefiles(self):
        Posts.postsxml.write(self.postsfile)
        with open(self.procpfile, 'w') as f:
            for id in self.procp:
                f.write(id + ',')
    def index(self, subreddit):
        logp('Started indexing')
        Posts.posts = ET.Element('posts')
        start = int(datetime(2018, 1, 1).timestamp())
        (postsjson, start) = getPushshiftData(sub= subreddit, after= start)
        postsarray = postsjson['data']
        logp('Pushshift search: ' + str(start) + ' ' + 'totalposts: ' + str(len(postsarray)))
        while start is not None:
            (postsjson, start) = getPushshiftData(sub= subreddit, after= start)
            if start is not None:
                postsarray.extend(postsjson['data'])
                logp('Pushshift search: ' + str(start) + ' ' + 'totalposts: ' + str(len(postsarray)))
        logp('Finished querrying for posts')
        for subm in postsarray:
            indexpostjson(subm, self)
        Posts.postsxml = ET.ElementTree(Posts.posts)
        Posts.postsxml.write(self.postsfile)
        logp('Finished indexing posts')
