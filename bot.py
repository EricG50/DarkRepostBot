import praw
import os.path
import time
import xml.etree.ElementTree as ET
from datetime import datetime
import keyboard

name ='darkrepostbot'
procpf = "processedposts.txt"
replystr = 'This is a repost. I found this {0} times. Best match {1} {2}. \n Report error in chat'

reddit = praw.Reddit(client_id = "mSk2wE1LwPilxg",
                     client_secret = "HVwC1jqHZA_PL6N7mIUL2_qWMhQ",
                     password='Jupiter.2004',
                     user_agent='u/darkrepostbot',
                     username= name
                     )

bigbookpost = reddit.submission(url= "https://www.reddit.com/r/darkjokes/comments/d8ptjx/the_big_book_of_reposts/")
announcements = reddit.submission(url= "https://www.reddit.com/r/darkjokes/comments/exspu7/announcement/")

pindex = ET.parse('posts.xml')
root = pindex.getroot()

darkjk = reddit.subreddit("darkjokes")

logf = open("log.txt", 'a')
logstr = '[{0}]: {1}\n'

def log(message):
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
        pindex.write('posts.xml')
        print("Finished processing. Hold q to exit")
        time.sleep(1)
        if keyboard.is_pressed('q'):
            break
        time.sleep(5)

    print("Exiting")
    log("Exiting")

    pindex.write('posts.xml')

    with open(procpf, 'w') as f:
        for id in procp:
            f.write(id + ',')

def loop(procp, bigbook):
    for subm in darkjk.new(limit=10):
        if subm.id not in procp and subm.id != bigbookpost.id and subm.id != announcements.id:
            log("Processing post " + subm.id)            
            processpost(subm)
            log("Processed post " + subm.id)
            procp.append(subm.id)

def processpost(subm):
    titlewords1 = subm.title.lower().split(' ')
    textwords1 = subm.selftext.lower().split(' ')

    repost = False
    found = 0
    bestmatch = 0
    bestmatchid = ''

    twc1 = len(titlewords1)
    textwc1 = len(textwords1)
    for p in root:
        title = p[0].text
        text = p[1].text

        titlewords2 = title.split(' ')
        textwords2 = text.split(' ')
        twc2 = len(titlewords2)
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
            textmatch = (float(textmwords) / max(textwc1, textwc2)) * 100

            match = (titlematch + textmatch) / 2

            if match == 100:
                found = found + 1
                log('Found exact match ')
                repost = True
            elif match > 80:
                found = found + 1
                log('Found close match ' + str(match))
                repost = True
            
            if match > bestmatch:
                bestmatch = match
                bestmatchid = p[2].text
    if repost:
        log('Post is a repost, url: ' + subm.shortlink)
        bm = reddit.submission(id= bestmatchid)
        url = bm.shortlink
        reply = replystr.format(found, bestmatch, url)
        subm.reply(reply)
        log('Replied ' + reply)
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