import praw
import os.path
import time
import xml.etree.ElementTree as ET
from datetime import datetime
import json
from pushshift import *
from util import *
from stats import Stats


name ='darkrepostbot'
procpf = "processedposts.txt"
dataxml = 'data.xml'
postsxml = 'posts.xml'

data = ET.parse(dataxml)
dataroot = data.getroot()

secret = dataroot.find('secret').text
password = dataroot.find('password').text
replogstr = dataroot.find('replogstr').text
replystr = dataroot.find('replystr').text

reddit = praw.Reddit(client_id = "mSk2wE1LwPilxg",
                     client_secret= secret,
                     password=password,
                     user_agent='u/darkrepostbot',
                     username= name
                     )

darkjk = reddit.subreddit('darkjokes')
statspost = reddit.submission(url='https://www.reddit.com/r/darkrepostbot/comments/f7hf89/statistics/')

st = Stats()
ps = Posts()

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

def main():
    
    logp("\nStarting bot")

    if reddit.user.me() == name:
        logp("connection ok")
    else:
        logp("failed to connect")
        return
    
    while True:
        print("Started processing")
        loop()
        ps.ind = False
        ps.writefiles()
        print("Finished processing")
        time.sleep(5)

    print("Exiting")
    logp("Exiting")

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

    indexedposts = 0
    
    for p in ps.posts:
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
    st.indposts = indexedposts
    if repost:
        if subm.id in matches:
            print('Error processed post wich was already on index')
            log('Error processed post wich was already on index')
            log('Post is not a repost')
            return
        bm = reddit.submission(id= bestmatchid)
        st.reposts = st.reposts + 1
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
            logp('Replied succesfully')
        except:
            logp('Error replying')
        
        try:
            lgs = replogstr.format(rp.shortlink, rp.title, rp.selftext, op.shortlink, op.title, op.selftext, bestmatch)
            with open('replog.txt', 'a') as rep:
                rep.write(lgs)
        except:
            logp('Error logging repost')
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

def loop():
    if ps.ind:
        logp('Started indexing')
        start = int(datetime(2018, 1, 1).timestamp())
        (postsjson, start) = getPushshiftData(sub= 'darkjokes', after= start)
        postsarray = postsjson['data']
        logp('Pushshift search: ' + str(start) + ' ' + 'totalposts: ' + str(len(postsarray)))
        while start is not None:
            (postsjson, start) = getPushshiftData(sub= 'darkjokes', after= start)
            if start is not None:
                postsarray.extend(postsjson['data'])
                logp('Pushshift search: ' + str(start) + ' ' + 'totalposts: ' + str(len(postsarray)))
        logp('Finished querrying for posts')
        submlist = getPosts(postsarray)
        logp('Finished getting posts')
        logp('Started indexing posts')
        for sub in submlist:
            subm = reddit.submission(id= sub)
            indexpost(subm)
        logp('Finished indexing posts')
    else:
        submlist = darkjk.new(limit= 50)
        ps.processposts(submlist, processpost, log)
        st.procposts = len(ps.procp)
        st.uploadstats(statspost)
        st.writexml()

def indexpost(subm):
    post = ET.SubElement(ps.posts, 'Post')
	
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
