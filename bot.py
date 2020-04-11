import praw
import os
import time
import xml.etree.ElementTree as ET
import threading
from datetime import datetime
from util import *
from stats import Stats
from log import *
from posts import Posts
import sys

procpf = "processedposts.txt"
dataxml = 'data.xml'
postsxml = 'posts.xml'

data = ET.parse(dataxml)
dataroot = data.getroot()

name = dataroot.find('username').text
secret = dataroot.find('secret').text
password = dataroot.find('password').text
#replogstr = dataroot.find('replogstr').text
replystr = dataroot.find('replystr').text
sub = dataroot.find('subreddit').text
client_id = dataroot.find('clientid').text

reddit = praw.Reddit(client_id = client_id,
                     client_secret= secret,
                     password=password,
                     user_agent='darkrepostbot',
                     username= name
                     )

darkjk = reddit.subreddit(sub)
statspost = reddit.submission(url=dataroot.find('statspost').text)

st = Stats(statspost)
ps = Posts(sub)
plog = ProcessedLogger()

def refresh():
    logp('Started refresh thread')
    while True:
        time.sleep(1850)
        try:
            reddit = praw.Reddit(client_id = client_id,
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
            exit(1)

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
        logerror(str(e))
        logp("Exiting")
        exit(1)
    except KeyboardInterrupt:
        logp('Intrerrupted, exiting')
        exit(0)

def exit(code):
    ps.writefiles()
    st.writefile()
    plog.write()
    os._exit(code)
    
def comment(text, post):
    try:
        #post.reply(text)
        logp('Replied succesfully')
    except Exception as e:
        logerror("Couldn't reply: " + str(e))

def processpost(subm):
    title1 = subm.title
    text1 = subm.selftext
    

    lastseenurl = ''
    lastseentime = 0
    firstseenurl = ''
    firstseentime = subm.created_utc

    logobj = {
        'title': title1,
        'author': subm.author.name,
        'time': subm.created_utc,
        'url': subm.shortlink,
        'bestmatch': {},
        'closematches': [],
        'repost': False
    }

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
            logobj['closematches'].append({ 'url': idtoUrl(matchid), 'match': match, 'time': int(p.find('Time').text) })
            found += found + 1
            if match == 100:
                log('Found exact match ' + idtoUrl(matchid))
                repost = True
            else:
                log('Found close match ' + str(match) + ' ' + idtoUrl(matchid))
                repost = True
        if match > bestmatch:
            bestmatch = match
            bestmatchid = matchid
    
    logobj['repost'] = repost
    logobj['bestmatch'] = { 'url': idtoUrl(bestmatchid), 'match': bestmatch }
    plog.logprocessed(logobj)

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

        plog.logrepost(logobj)

        for match in logobj['closematches']:
            t = match['time']
            if t > lastseentime:
                lastseentime = t
                lastseenurl = match['url']
            if t < firstseentime:
                firstseentime = t
                firstseenurl = match['url']
        
        plural = ''
        if found > 1:
            plural = 's'
        fs = datetime.utcfromtimestamp(firstseentime)
        ls = datetime.utcfromtimestamp(lastseentime)
        fplink = f'https://www.reddit.com/message/compose?to=/r/darkrepostbot&subject=False-positive&message=False-positive, url:{rp.shortlink}'
        reply = replystr.format(found, bestmatch, op.shortlink, plural, firstseenurl,
                                fs.strftime('%d/%m/%Y %H:%M:%S'), lastseenurl,
                                ls.strftime('%d/%m/%Y %H:%M:%S'), len(ps.posts), fplink)
        log('Replying:\n' + reply)
        
        comment(reply, rp)

        try:
            rp.downvote()
        except:
            logerror("Couldn't downvote")

        # try:
        #     lgs = replogstr.format(rp.shortlink, rp.title, rp.selftext, op.shortlink, op.title, op.selftext, bestmatch)
        #     with open('replog.txt', 'a') as rep:
        #         rep.write(lgs)
        # except:
        #     logerror('Error logging repost')
        #     try:
        #         with open('replog.txt', 'a') as rep:
        #             lgs = replogstr.format(rp.shortlink, 'Error', 'Error', op.shortlink, 'Error', 'Error', bestmatch)
        #             rep.write(lgs)
        #     except:
        #         pass
    else:
        log('Post is NOT a repost. Bestmatch: ' + str(bestmatch) + ' ' + idtoUrl(bestmatchid))

    if not present:
        indexpost(subm, ps)

def loop():
    submlist = darkjk.new(limit= 50)
    ps.processposts(submlist, processpost)
    plog.write()
    st.procposts = len(ps.procp)
    st.indposts = len(ps.posts)
    
if __name__== "__main__":
    main()
