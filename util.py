import praw
import os.path
import xml.etree.ElementTree as ET

class Posts:
    ind = False
    postsfile = 'posts.xml'
    procpfile = 'processedposts.txt'
    def __init__(self):
        if not os.path.isfile(self.postsfile):
            self.ind = True
            with open(self.postsfile, 'a') as w:
                w.write('<posts></posts>')
        if not os.path.isfile(self.procpfile):
            f = open(self.procpfile, 'a')
            f.close()
        self.postsxml = ET.parse(self.postsfile)
        self.posts = self.postsxml.getroot()
        with open(self.procpfile, 'r') as f:
            procpstr = f.read()
        procpstr.strip()
        self.procp = procpstr.split(',')
        self.procp.remove('')
    def processposts(self, posts, method, log):
        for subm in posts:
            if subm.id not in self.procp and subm.is_self:
                log("Processing post " + subm.id + ' ' + subm.shortlink)            
                method(subm)
                self.procp.append(subm.id)
    def writefiles(self):
        self.postsxml.write(self.postsfile)
        with open(self.procpfile, 'w') as f:
            for id in self.procp:
                f.write(id + ',')