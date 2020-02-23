import praw
import os.path
import time
import xml.etree.ElementTree as ET
from datetime import datetime
import json
from pushshift import *
from statuploader import *

name ='darkrepostbot'
procpf = "processedposts.txt"
statfile = 'stat.xml'
postsxml = 'posts.xml'
dataxml = 'data.xml'

data = ET.parse(dataxml)
dataroot = data.getroot()

secret = dataroot.find('secret').text
password = dataroot.find('password').text

replogstr = 'repost: \n url: {0} \n title: {1} \n text: {2} \noriginalpost: \n url: {3} \n title: {4} \n text: {5} \n match: {6} \n \n'
replystr = '**This is a repost**. I found this {0} time{3}.    \nBest match: {1}% {2}.    \nFirst seen [here]({4}) {5}    \nLast seen [here]({6}) {7}    \n\nIndexed posts: {8} r/darkrepostbot'

reddit = praw.Reddit(client_id = "mSk2wE1LwPilxg",
                     client_secret= secret,
                     password=password,
                     user_agent='u/darkrepostbot',
                     username= name
                     )

darkjk = reddit.subreddit('darkjokes')
stats = reddit.submission(url='https://www.reddit.com/r/darkrepostbot/comments/f7hf89/statistics/')

logstr = '[{0}]: {1}\n'

indexedposts = 0
reposts = 0

def log(message):
    #print(message)
    with open("log.txt", 'a') as logf:
        time = datetime.utcnow()
        logf.write(logstr.format(time.strftime("%d/%m/%Y %H:%M:%S"), message))

def main():

    log("\nStarting bot")

    if reddit.user.me() == name:
        print("connection ok")
    else:
        print("failed to connect")
        return

    log("Connected to reddit")

    ind = False
    
    if not os.path.isfile(postsxml):
        ind = True
        with open(postsxml, 'a') as w:
           w.write('<posts></posts>')
    
    if not os.path.isfile(statfile):
        with open(statfile, 'a') as w:
           w.write('<statistics></statistics>')
    
    pindex = ET.parse(postsxml)
    global root
    root = pindex.getroot()

    statxml = ET.parse(statfile)
    global stat
    stat = statxml.getroot()

    reposts = int(stat.find('repostsfound').text)

    if not os.path.isfile(procpf):
        f = open(procpf, 'a')
        f.close()
    with open(procpf, 'r') as f:
        procpstr = f.read()
    procpstr.strip()
    procp = procpstr.split(',')
    procp.remove('')
    
    while True:
        print("Started processing")
        loop(procp, ind)
        ind = False
        statxml.write(statfile)
        pindex.write(postsxml)
        with open(procpf, 'w') as f:
            for id in procp:
                f.write(id + ',')
        print("Finished processing")
        time.sleep(5)

    print("Exiting")
    log("Exiting")

def loop(procp, ind):
    if ind:
        log('Started indexing')
        start = int(datetime(2018, 1, 1).timestamp())
        (postsjson, start) = getPushshiftData(sub= 'darkjokes', after= start)
        postsarray = postsjson['data']
        log('Pushshift search: ' + str(start) + ' ' + 'totalposts: ' + str(len(postsarray)))
        while start is not None:
            (postsjson, start) = getPushshiftData(sub= 'darkjokes', after= start)
            log('Pushshift search: ' + str(start) + ' ' + 'totalposts: ' + str(len(postsarray)))
            if start is not None:
                postsarray.extend(postsjson['data'])
        log('Finished querrying for posts')
        submlist = getPosts(postsarray)
        log('Finished getting posts')
        log('Started indexing posts')
        for sub in submlist:
            subm = reddit.submission(id= sub)
            indexpost(subm)
        log('Finished indexing posts')
    else:
        submlist = darkjk.new(limit= 50)
        procposts(submlist, procp)
        inp = stat.find('indexedposts')
        reposts = stat.find('repostsfound')
        procpost = stat.find('processedposts')
        inp.text = str(indexedposts)
        reposts.text = str(reposts)
        procpost.text = str(len(procp))
        uploadstats(stats, stat)


def procposts(submlist, procp):
    for subm in submlist:
        if subm.id not in procp and subm.is_self:
            log("Processing post " + subm.id + ' ' + subm.shortlink)            
            processpost(subm)
            log("Processed post " + subm.id)
            procp.append(subm.id)

def processpost(subm):
    titlewords1 = subm.title.strip().lower().split(' ')
    text1 = subm.selftext
    textwc1 = 0
    twc1 = len(titlewords1)

    lastseenurl = ''
    lastseentime = 0
    firstseenurl = ''
    firstseentime = subm.created_utc

    matches = []

    if type(text1) is str:
        textwords1 = text1.strip().lower().split(' ')
        textwc1 = len(textwords1)

    repost = False
    found = 0
    bestmatch = 0
    bestmatchid = ''
    
    for p in root:
        indexedposts = indexedposts + 1

        title = p[0].text
        text2 = p[1].text

        titlewords2 = title.split(' ')
        twc2 = len(titlewords2)

        textwc2 = 0
        if type(text2) is str:
            textwords2 = text2.split(' ')
            textwc2 = len(textwords2)
        
        titlemwords = 0
        textmwords = 0
        if abs(twc1 - twc2) < max(twc1, twc2) / 3:
            for i in range(0, min(twc1, twc2)):
                if titlewords1[i].strip() == titlewords2[i].strip():
                    titlemwords = titlemwords + 1

            for i in range(0, min(textwc1, textwc2)):
                if textwords1[i].strip() == textwords2[i].strip():
                    textmwords = textmwords + 1

            titlematch = (float(titlemwords) / max(twc1, twc2)) * 100
            if max(textwc1, textwc2) != 0:
                textmatch = (float(textmwords) / max(textwc1, textwc2)) * 100
            else:
                textmatch = titlematch

            match = (titlematch + textmatch) / 2

            if match > 85:
                if match == 100:
                    found = found + 1
                    log('Found exact match ' + p[2].text)
                    repost = True
                else:
                    found = found + 1
                    log('Found close match ' + str(match) + ' ' + p[2].text)
                    repost = True
                matches.append(p[2].text)
            
            if match > bestmatch:
                bestmatch = match
                bestmatchid = p[2].text
    if repost:
        if subm.id in matches:
            print('Error processed post wich was already on index')
            log('Error processed post wich was already on index')
            log('Post is not a repost')
            return
        bm = reddit.submission(id= bestmatchid)
        reposts = reposts + 1
        if bm.created_utc > subm.created_utc:
            op = subm
            rp = bm
            log("Found a repost of this " + rp.shortlink)
        else:
            op = bm
            rp = subm
        indexpost(subm)
        log('Indexed post ' + subm.id)
        log('Post is a repost, url: ' + rp.shortlink)
        print('Found repost')

        for m in matches:
            mp = reddit.submission(id= m)
            t = mp.created_utc
            if t > lastseentime:
                lastseentime = t
                lastseenurl = mp.shortlink
            if t < firstseentime:
                firstseentime = t
                firstseenurl = mp.shortlink
        
        url = op.shortlink
        pl = ''
        if found > 1:
            pl = 's'
        fs = datetime.utcfromtimestamp(firstseentime)
        ls = datetime.utcfromtimestamp(lastseentime)
        reply = replystr.format(found, bestmatch, url, pl, firstseenurl, fs.strftime('%d/%m/%Y %H:%M:%S'), lastseenurl, ls.strftime('%d/%m/%Y %H:%M:%S'), indexedposts)
        log('Replying ' + reply)
        try:
            rp.reply(reply)
            log('Replied succesfully')
            print('Replied succesfully')
        except:
            log('Error replying')
            print('Error replying')
        
        try:
            lgs = replogstr.format(rp.shortlink, rp.title, rp.selftext, op.shortlink, op.title, op.selftext, bestmatch)
            with open('replog.txt', 'a') as rep:
                rep.write(lgs)
        except:
            log('Error logging repost')
            print('Error logging repost')
            try:
                with open('replog.txt', 'a') as rep:
                    lgs = replogstr.format(rp.shortlink, 'Error', 'Error', op.shortlink, 'Error', 'Error', bestmatch)
                    rep.write(lgs)
            except:
                return
    else:
        log('Post is not a repost')
        indexpost(subm)
        log('Indexed post')

def indexpost(subm):
    post = ET.SubElement(root, 'Post')
	
    title = subm.title.strip()
    text = subm.selftext.strip()

    ptitle = ET.SubElement(post, 'Title')
    ptitle.text = title.lower()
    ptext = ET.SubElement(post, 'Text')
    ptext.text = text.lower()
    pid = ET.SubElement(post, 'Id')
    pid.text = subm.id
    
if __name__== "__main__":
    main()
