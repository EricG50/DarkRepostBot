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

class ErrLog:
    file = 'err.json'
    @classmethod
    def load(cls):
        if os.path.isfile(cls.file):
            with open(cls.file, 'r') as f:
                cls.errors = json.load(f)
        else:
            cls.errors = { 'errors': [] }
            with open(cls.file, 'w') as f:
                json.dump(cls.errors, f, indent=4)
    @classmethod
    def log(cls, err, sev, context=None):
        logp('Error: ' + err)
        time = datetime.utcnow()
        with open('err.txt', 'a') as logf:
            logf.write(logstr.format(time.strftime("%d/%m/%Y %H:%M:%S"), err))
        logobj = {
            'time': time.timestamp(),
            'error': err,
            'context': context,
            'severity': sev
        }
        cls.errors['errors'].append(logobj)
        with open(cls.file, 'w') as f:
            json.dump(cls.errors, f, indent=4)

class ProcessedLogger:
    logfile = 'procplog.json'
    def __init__(self):
        if os.path.isfile(self.logfile):
            with open(self.logfile, 'r') as f:
                self.posts = json.load(f)
        else:
            self.posts = { 'reposts': [], 'processedposts': [], 'falsepositives': [], 'potentialreposts': [] }
    def logprocessed(self, logobj):
        self.posts['processedposts'].append(logobj)
    def logrepost(self, logobj):
        self.posts['reposts'].append(logobj)
    def logfalsepos(self, logobj):
        self.posts['falsepositives'].append(logobj)
    def logpotrepost(self, logobj):
        self.posts['potentialreposts'].append(logobj)
    def write(self):
        with open(self.logfile, 'w') as f:
            json.dump(self.posts, f, indent=4)