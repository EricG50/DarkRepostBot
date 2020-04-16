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
from server import Server
import sys

dataxml = 'data.xml'

data = ET.parse(dataxml)
dataroot = data.getroot()

name = dataroot.find('username').text
secret = dataroot.find('secret').text
password = dataroot.find('password').text
replystr = dataroot.find('replystr').text
statstr = dataroot.find('statsformat').text
sub = dataroot.find('subreddit').text
client_id = dataroot.find('clientid').text
port = int(dataroot.find('port').text)

reddit = praw.Reddit(client_id = client_id,
                     client_secret= secret,
                     password=password,
                     user_agent='darkrepostbot',
                     username= name
                     )

darkjk = reddit.subreddit(sub)
statspost = reddit.submission(url=dataroot.find('statspost').text)

class ServerEventHandler:
    @classmethod
    def ReportFalsePositive(cls, body) -> int:
        id = body['id']
        message = body['message']
        sender = body['sender']
        logp(f'Recieved false positive report ID:{id} Message: {message} from {sender}')
        for i, repost in enumerate(plog.posts['reposts']):
            rid = repost['url'].split('/')[-1]
            if rid == id:
                repost['falsePositive'] = True
                repost['falsePositivemessage'] = message
                plog.posts['reposts'][i] = repost
                plog.logfalsepos(repost)
                logp('Report accepted')
                st.falsepos += 1
                #st.uploadstats()
                try:
                    repostcom = reddit.comment(id= repost['commentId'])
                    repostcom.reply('It has been determined that this is a false positive. Sorry for the error')
                except:
                    logerror('Failed to reply', 3, "False positive reply")
                return 200
        logp('Report rejected')
        return 400

ps = Posts(sub)
st = Stats(statspost, statstr)
plog = ProcessedLogger()
Server.start(port=port, repfalsepos=ServerEventHandler.ReportFalsePositive)

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
            logerror('Failed to refresh reddit', 5)

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
        logerror(str(e), 10)
        logp("Critical error has occured. Waiting for shutdown request")
        try:
            Server.waitforexit()
        except KeyboardInterrupt:
            pass
        exit(1)
    except KeyboardInterrupt:
        logp('Intrerrupted, exiting')
        Server.exit()
        exit(0)

def exit(code):
    ps.writefiles()
    st.writefile()
    plog.write()
    os._exit(code)

def comment(text, post):
    try:
        com = post.reply(text)
        logp('Replied succesfully')
        return com.id
    except Exception as e:
        logerror("Couldn't reply: " + str(e), 4, "Replying to a repost")
        return None

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
        'commentId': None,
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
            logobj['closematches'].append({ 'url': idtoUrl(matchid), 'match': match, 'time': float(p.find('Time').text) })
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
        reportmessage = f"""{{report: {{ reason: "false-positive", url: "{rp.shortlink}" }}}}"""
        fplink = f'https://www.reddit.com/message/compose?to=/r/darkrepostbot&subject=False-positive&message=' + reportmessage
        reply = replystr.format(found, bestmatch, op.shortlink, plural, firstseenurl,
                                fs.strftime('%d/%m/%Y %H:%M:%S'), lastseenurl,
                                ls.strftime('%d/%m/%Y %H:%M:%S'), len(ps.posts), fplink)
        log('Replying:\n' + reply)
        logobj['commentId'] = comment(reply, rp)

        plog.logrepost(logobj)

        try:
            rp.downvote()
        except:
            logerror("Couldn't downvote", 2)

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

    plog.logprocessed(logobj)

    if not present:
        indexpost(subm, ps)

def loop():
    submlist = darkjk.new(limit= 50)
    ps.processposts(submlist, processpost)
    plog.write()
    st.procposts = len(ps.procp)
    st.indposts = len(ps.posts)
    st.writefile()

if __name__== "__main__":
    main()
