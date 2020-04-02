import praw
import os.path
import time
import xml.etree.ElementTree as ET
from datetime import datetime
import json
from pushshift import *
from util import *
from stats import Stats
from log import *
import requests

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

ps = Posts()
st = Stats(statspost)

def main():
    
    logp("\nStarting bot")

    if reddit.user.me() == name:
        logp("connection ok")
    else:
        logp("failed to connect")
        return
    
    try:
        while True:
            print("Started processing")
            loop()
            print("Finished processing")
            time.sleep(5)
    except Exception as e:
        st.write()
        ps.writefiles()
        raise e

    st.write()
    ps.writefiles()
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
    
    for p in ps.posts:
        if p['id'] == subm.id:
            continue
        if not 'title' in p or not 'selftext' in p:
            continue
        title2 = p['title']
        text2 = p['selftext']

        titlewords2 = title2.split(' ')
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
                found = found + 1
                if match == 100:
                    log('Found exact match ' + p['url'])
                    repost = True
                else:
                    log('Found close match ' + str(match) + ' ' + p['url'])
                    repost = True
                matches.append(p['id'])
            if match > bestmatch:
                bestmatch = match
                bestmatchid = p['id']
    if repost:
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
        logp('Post is a repost, url: ' + rp.shortlink)

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
        reply = replystr.format(found, bestmatch, url, pl, firstseenurl, fs.strftime('%d/%m/%Y %H:%M:%S'), lastseenurl, ls.strftime('%d/%m/%Y %H:%M:%S'))
        log('Replying: ' + reply)
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
    submlist = darkjk.new(limit= 200)
    ps.processposts(submlist, processpost)
    st.indposts = len(ps.posts)
    st.procposts = len(ps.procp)
    st.write()

def indexpost(subm):
    url = 'https://api.pushshift.io/reddit/search/submission/?id=' + subm.id
    r = requests.get(url)
    data = json.loads(r.content)
    ps.posts.append(data['data'][0])
    
if __name__== "__main__":
    main()
