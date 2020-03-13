import praw
import os.path
import xml.etree.ElementTree as ET
from datetime import datetime

class Stats:
    statfile = 'stat.xml'
    reposts = 0
    indposts = 0
    procposts = 0
    def __init__(self):
        if not os.path.isfile(self.statfile):
            with open(self.statfile, 'a') as w:
                w.write('<statistics><indexedposts>0</indexedposts><repostsfound>0</repostsfound><processedposts>0</processedposts></statistics>')
        self.statxml = ET.parse(self.statfile)
        self.stat = self.statxml.getroot()
        self.inp = self.stat.find('indexedposts')
        self.rep = self.stat.find('repostsfound')
        self.pp = self.stat.find('processedposts')
        self.reposts = int(self.rep.text)
        self.indposts = int(self.inp.text)
        self.procposts = int(self.pp.text)
    def uploadstats(self, statspost):
        nl = '    \n'
        repostsrate = str((float(self.reposts) / self.procposts) * 100)
        time = datetime.utcnow()
        statstring = 'Indexed posts: ' + str(self.indposts) + nl + 'Reposts found: ' + str(self.reposts) + nl + 'Processed posts: ' + str(self.procposts) + nl + 'Repost rate: ' + repostsrate + '%' + nl + 'Updated: ' + time.strftime("%d/%m/%Y %H:%M:%S")
        statspost.edit(statstring)
    def writexml(self):
        self.inp.text = str(self.indposts)
        self.rep.text = str(self.reposts)
        self.pp.text = str(self.procposts)
        self.statxml.write(self.statfile)


