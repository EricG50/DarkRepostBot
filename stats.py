import praw
import json
import os.path
import xml.etree.ElementTree as ET
import threading
import time
from datetime import datetime
from log import *

class Stats:
    statfile = 'stat.json'
    reposts = 0
    indposts = 0
    procposts = 0
    statsjson = {
        'reposts' : 0,
        'indposts' : 0,
        'procposts' : 0
    }
    def __init__(self, statspost):
        if not os.path.isfile(self.statfile):
            json.dump(self.statsjson, open(self.statfile, 'w'))
        else:
            self.statsjson = json.load(open(self.statfile, 'r'))
        self.reposts = int(self.statsjson['reposts'])
        self.indposts = int(self.statsjson['indposts'])
        self.procposts = int(self.statsjson['procposts'])
        self.statspost = statspost
        self.updatethread = threading.Thread(target=self.updatefunc)
        self.updatethread.start()
    def updatefunc(self):
        while True:
            time.sleep(10)
            if(self.procposts > 0):
                self.uploadstats()
                logp('Updated stats')
    def uploadstats(self):
        nl = '    \n'
        repostsrate = str((float(self.reposts) / self.procposts) * 100)
        time = datetime.utcnow()
        statstring = 'Indexed posts: ' + str(self.indposts) + nl + 'Reposts found: ' + str(self.reposts) + nl + 'Processed posts: ' + str(self.procposts) + nl + 'Repost rate: ' + repostsrate + '%' + nl + 'Updated: ' + time.strftime("%d/%m/%Y %H:%M:%S")
        self.statspost.edit(statstring)
    def write(self):
        self.statsjson = {
            'reposts' : self.reposts,
            'indposts' : self.indposts,
            'procposts' : self.procposts
        }
        json.dump(self.statsjson, open(self.statfile, 'w'))