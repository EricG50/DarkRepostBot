import praw
import xml.etree.ElementTree as ET
from datetime import datetime

nl = '    \n'

def uploadstats(statspost, statsxml):
    inp = statsxml.find('indexedposts').text
    reposts = statsxml.find('repostsfound').text
    procp = statsxml.find('processedposts').text
    #repostsrate = str((float(reposts) / int(procp)) * 100)
    time = datetime.utcnow()
    statstring = 'Indexed posts: ' + inp + nl + 'Reposts found: ' + reposts + nl + 'Processed posts: ' + procp + 'Updated: ' + time.strftime("%d/%m/%Y %H:%M:%S")
    statspost.edit(statstring)