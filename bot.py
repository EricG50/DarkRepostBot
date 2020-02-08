import praw
import os.path
import time
import xml.etree.ElementTree as ET
from datetime import datetime
import keyboard

name ='darkrepostbot'
procpf = "processedposts.txt"
replystr = 'This is a repost. I found this {0} times. Best match {1} {2}. \n Report error in chat'
postsxml = 'posts.xml'

replogstr = 'repost: \n url: {0} \n title: {1} \n text: {2} \noriginalpost: \n url: {3} \n title: {4} \n text: {5} \n match: {6} \n \n'

reddit = praw.Reddit(client_id = "mSk2wE1LwPilxg",
                     client_secret = "HVwC1jqHZA_PL6N7mIUL2_qWMhQ",
                     password='Jupiter.2004',
                     user_agent='u/darkrepostbot',
                     username= name
                     )

bigbookpost = reddit.submission(url= "https://www.reddit.com/r/darkjokes/comments/d8ptjx/the_big_book_of_reposts/")
announcements = reddit.submission(url= "https://www.reddit.com/r/darkjokes/comments/exspu7/announcement/")

darkjk = reddit.subreddit("darkjokes")

logstr = '[{0}]: {1}\n'

def log(message):
    with open("log.txt", 'a') as logf:
        time = datetime.utcnow()
        logf.write(logstr.format(time.strftime("%d/%m/%Y %H:%M:%S"), message))

def main():

    log("Starting bot")

    if reddit.user.me() == name:
        print("connection ok")
    else:
        print("failed to connect")
        return

    log("Connected to reddit")

    if not os.path.isfile(postsxml):
       with open('posts.xml', 'a') as w:
           w.write('<posts></posts>')
    
    pindex = ET.parse(postsxml)
    global root
    root = pindex.getroot()

    if not os.path.isfile(procpf):
        f = open(procpf, 'a')
        f.close()
    with open(procpf, 'r') as f:
        procpstr = f.read()
    procpstr.strip()
    procp = procpstr.split(',')
    procp.remove('')

    bigb = bigbookpost.selftext
    bigb.strip()
    bigb = bigb.lower()
    bigbook = bigb.split('-')
    del bigbook[0:2]
    del bigbook[-1]
    
    while True:
        print("Started processing")
        loop(procp, bigbook)
        pindex.write(postsxml)
        with open(procpf, 'w') as f:
            for id in procp:
                f.write(id + ',')
        print("Finished processing")
        time.sleep(5)

    print("Exiting")
    log("Exiting")

def loop(procp, bigbook):
    dnew = darkjk.new(limit= 50)
    dhot = darkjk.hot(limit= 50)
    dtop = darkjk.top(limit= 50)

    for subm in dnew:
        if subm.id not in procp and subm.id != bigbookpost.id and subm.id != announcements.id:
            log("Processing post " + subm.id)            
            processpost(subm, bigbook)
            log("Processed post " + subm.id)
            procp.append(subm.id)
    
    for subm in dhot:
        if subm.id not in procp and subm.id != bigbookpost.id and subm.id != announcements.id:
            log("Processing post " + subm.id)            
            processpost(subm, bigbook)
            log("Processed post " + subm.id)
            procp.append(subm.id)

    for subm in dtop:
        if subm.id not in procp and subm.id != bigbookpost.id and subm.id != announcements.id:
            log("Processing post " + subm.id)            
            processpost(subm, bigbook)
            log("Processed post " + subm.id)
            procp.append(subm.id)

def processpost(subm, bigbook):
    titlewords1 = subm.title.lower().split(' ')
    text1 = subm.selftext.lower()
    textwc1 = 0
    twc1 = len(titlewords1)

    if type(text1) is str:
        textwords1 = text1.split(' ')
        textwc1 = len(textwords1)

    repost = False
    found = 0
    bestmatch = 0
    bestmatchid = ''
    
    
    for p in root:
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
        if abs(twc1 - twc2) < max(twc1, twc2) / 4:
            for i in range(0, min(twc1, twc2)):
                if titlewords1[i] == titlewords2[i]:
                    titlemwords = titlemwords + 1

            for i in range(0, min(textwc1, textwc2)):
                if textwords1[i] == textwords2[i]:
                    textmwords = textmwords + 1

            titlematch = (float(titlemwords) / max(twc1, twc2)) * 100
            if max(textwc1, textwc2) != 0:
                textmatch = (float(textmwords) / max(textwc1, textwc2)) * 100
            else:
                textmatch = titlematch

            match = (titlematch + textmatch) / 2

            if match == 100:
                found = found + 1
                log('Found exact match ')
                repost = True
            elif match > 90:
                found = found + 1
                log('Found close match ' + str(match))
                repost = True
            
            if match > bestmatch:
                bestmatch = match
                bestmatchid = p[2].text
    if repost:
        bm = reddit.submission(id= bestmatchid)
        if bm.created_utc > subm.created_utc:
            op = subm
            rp = bm
            log("Found a repost of this " + rp.shortlink)
            indexpost(op)
            log('Indexed post ' + op.id)
        else:
            op = bm
            rp = subm
        log('Post is a repost, url: ' + rp.shortlink)
        print('Found repost')
        
        url = op.shortlink
        reply = replystr.format(found, bestmatch, url)
        log('Replying ' + reply)
        try:
            rp.reply(reply)
            log('Replied succesfully')
            print('Replied succesfully')
        except:
            log('Error replying')
            print('Error replying')
        
        with open('replog.txt', 'a') as rep:
            rep.write(replogstr.format(rp.shortlink, rp.title, rp.selftext, op.shortlink, op.title, op.selftext, bestmatch))
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