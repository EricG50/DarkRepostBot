import json
import os.path
from datetime import datetime

logstr = '[{0}]: {1}\n'
def log(message):
    with open("log.txt", 'a') as logf:
        time = datetime.utcnow()
        logf.write(logstr.format(time.strftime("%d/%m/%Y %H:%M:%S"), message))

def logp(message):
    print(message)
    with open("log.txt", 'a') as logf:
        time = datetime.utcnow()
        logf.write(logstr.format(time.strftime("%d/%m/%Y %H:%M:%S"), message))

def logerror(err):
    logp('Error: ' + err)
    with open("err.txt", 'a') as logf:
        time = datetime.utcnow()
        logf.write(logstr.format(time.strftime("%d/%m/%Y %H:%M:%S"), err))

class ProcessedLogger:
    logfile = 'procplog.json'
    def __init__(self):
        if os.path.isfile(self.logfile):
            with open(self.logfile, 'r') as f:
                self.posts = json.load(f)
        else:
            self.posts = { 'reposts': [], 'processedposts': [] }
    def logprocessed(self, logobj):
        self.posts['processedposts'].append(logobj)
    def logrepost(self, logobj):
        self.posts['reposts'].append(logobj)
    def write(self):
        with open(self.logfile, 'w') as f:
            json.dump(self.posts, f)