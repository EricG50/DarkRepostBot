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