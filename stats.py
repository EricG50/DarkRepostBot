import praw
import os.path
import xml.etree.ElementTree as ET
import time
import json
import threading
from log import *
from datetime import datetime

class Stats:
    statfile = 'stat.json'
    stats = {
        'reposts': 0,
        'indexedposts': 0,
        'processedposts': 0,
        'falsepostives': 0
    }
    def __init__(self, statspost, formatstring):
        if os.path.isfile(self.statfile):
            with open(self.statfile, 'r') as f:
                stats = json.load(f)
        self.formstr = formatstring
        self.statspost = statspost
        self.reposts = stats['reposts']
        self.indposts = stats['indexedposts']
        self.procposts = stats['processedposts']
        self.falsepos = stats['falsepostives']
        self.upThread = threading.Thread(target=self.uploadthread)
        self.upThread.start()

    def uploadstats(self):
        try:
            repostrate = str((float(self.reposts - self.falsepos) / self.procposts) * 100)
            errorrate = str((float(self.falsepos) / self.reposts) * 100)
            time = datetime.utcnow()
            statstring = self.formstr.format(self.indposts, self.reposts, self.procposts, repostrate, self.falsepos, errorrate, time.strftime('%d/%m/%Y %H:%M:%S'))
            self.statspost.edit(statstring)
            logp('Succesfully uploaded statistics')
        except:
            logerror('Failed to upload statistics')
        
    def writefile(self):
        self.stats['reposts'] = self.reposts
        self.stats['indexedposts'] = self.indposts
        self.stats['processedposts'] = self.procposts
        self.stats['falsepositives'] = self.falsepos
        with open(self.statfile, 'w') as f:
            json.dump(self.stats, f)
        
    def uploadthread(self):
        logp('Started stats uploader thread')
        while True:
            time.sleep(600)
            self.uploadstats()

