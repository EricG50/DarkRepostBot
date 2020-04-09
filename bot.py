import praw
import os
import time
import xml.etree.ElementTree as ET
import threading
from datetime import datetime
import json
from pushshift import *
from util import *
from stats import Stats
from log import *
from posts import Posts

procpf = "processedposts.txt"
dataxml = 'data.xml'
postsxml = 'posts.xml'

data = ET.parse(dataxml)
dataroot = data.getroot()

name = dataroot.find('username').text
secret = dataroot.find('secret').text
password = dataroot.find('password').text
replogstr = dataroot.find('replogstr').text
replystr = dataroot.find('replystr').text

reddit = praw.Reddit(client_id = "mSk2wE1LwPilxg",
                     client_secret= secret,
                     password=password,
                     user_agent='darkrepostbot',
                     username= name
                     )

darkjk = reddit.subreddit('darkjokes')
statspost = reddit.submission(url=dataroot.find('statspost').text)

st = Stats(statspost)
ps = Posts()

def refresh():
    logp('Started refresh thread')
    while True:
        time.sleep(1850)
        try:
            reddit = praw.Reddit(client_id = "mSk2wE1LwPilxg",
                    client_secret= secret,
                    password=password,
                    user_agent='darkrepostbot',
                    username= name
                    )
            logp('Refreshed reddit')
            if reddit.user.me() == name:
                logp("connection ok")
        except:
            logerror('Failed to refresh reddit. Terminating script')
            os._exit()

def main():
    logp("Starting bot")

    if reddit.user.me() == name:
        logp("connection ok")
    else:
        logerror("failed to connect")
        return
    
    refthread = threading.Thread(target=refresh)
    refthread.start()
    time.sleep(0.5)

    try:
        while True:
            print("Started processing")
            loop()
            print("Finished processing")
            time.sleep(30)
    except Exception as e:
        ps.writefiles()
        st.writefile()
        logerror(str(e))
        logp("Exiting")
        raise e

    logp("Exiting")

def processpost(subm):
    title1 = subm.title
    text1 = subm.selftext
    

    lastseenurl = ''
    lastseentime = 0
    firstseenurl = ''
    firstseentime = subm.created_utc

    matches = []

    repost = False
    present = False
    found = 0
    bestmatch = 0
    bestmatchid = ''
    
    for p in ps.posts:
        if p.find('Id').text == subm.id:
            present = True
            continue
        title2 = p.find('Title').text
        text2 = p.find('Text').text

        match = compareposts(title1, text1, title2, text2)

        matchid = p.find('Id').text
        if match > 85:
            matches.append(matchid)
            if match == 100:
                found = found + 1
                log('Found exact match ' + matchid)
                repost = True
            else:
                found = found + 1
                log('Found close match ' + str(match) + ' ' + matchid)
                repost = True
        if match > bestmatch:
            bestmatch = match
            bestmatchid = matchid
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
        fplink = f'/message/compose?to=/r/darkrepostbot&subject=False positive&message=False positive, url: {rp.shortlink}'
        reply = replystr.format(found, bestmatch, url, pl, firstseenurl, fs.strftime('%d/%m/%Y %H:%M:%S'), lastseenurl, ls.strftime('%d/%m/%Y %H:%M:%S'), len(ps.posts), fplink)
        log('Replying:\n' + reply)
        try:
            rp.reply(reply + ('Mods gay ' * 600))
            logp('Replied succesfully')
        except Exception as e:
            logerror("Couldn't reply: " + str(e))

        try:
            rp.downvote()
        except:
            logerror("Couldn't downvote")

        try:
            lgs = replogstr.format(rp.shortlink, rp.title, rp.selftext, op.shortlink, op.title, op.selftext, bestmatch)
            with open('replog.txt', 'a') as rep:
                rep.write(lgs)
        except:
            logerror('Error logging repost')
            try:
                with open('replog.txt', 'a') as rep:
                    lgs = replogstr.format(rp.shortlink, 'Error', 'Error', op.shortlink, 'Error', 'Error', bestmatch)
                    rep.write(lgs)
            except:
                pass
    else:
        log('Post is NOT a repost. Bestmatch: ' + str(bestmatch) + ' ' + str(bestmatchid))

    if not present:
        indexpost(subm, ps)

def loop():
    submlist = darkjk.new(limit= 50)
    ps.processposts(submlist, processpost)
    st.procposts = len(ps.procp)
    st.indposts = len(ps.posts)
    ps.writefiles()
    st.writefile()
    
if __name__== "__main__":
    main()
