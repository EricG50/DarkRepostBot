import praw
import os.path
import xml.etree.ElementTree as ET
from log import *
                
def indexpost(subm, ps):
    log('Indexed post' + subm.id)
    post = ET.SubElement(ps.posts, 'Post')
	
    title = subm.title
    text = subm.selftext

    ptitle = ET.SubElement(post, 'Title')
    ptitle.text = cleantext(title)
    ptext = ET.SubElement(post, 'Text')
    ptext.text = cleantext(text)
    pid = ET.SubElement(post, 'Id')
    pid.text = subm.id

def indexpostjson(subm, ps):
    post = ET.SubElement(ps.posts, 'Post')

    title = subm['title']
    text = ''
    if 'selftext' in subm:
        text = subm['selftext']

    ptitle = ET.SubElement(post, 'Title')
    ptitle.text = cleantext(title)
    ptext = ET.SubElement(post, 'Text')
    ptext.text = cleantext(text)
    pid = ET.SubElement(post, 'Id')
    pid.text = subm['id']

def cleantext(txt):
    return txt.strip().lower().replace('\u0012', '')

def cleansubmtext(txt):
    chars = "\\`*_{}[]()-.,!?"
    for c in chars:
        if c in txt:
            txt = txt.replace(c, '')
    return txt.strip().lower()

def compareposts(title1, text1, title2, text2):
    titlewords1 = cleansubmtext(title1).split(' ')
    textwc1 = 0
    twc1 = len(titlewords1)
    if type(text1) is str:
        textwords1 = cleansubmtext(text1).split(' ')
        textwc1 = len(textwords1)

    titlewords2 = cleansubmtext(title2).split(' ')
    twc2 = len(titlewords2)
    textwc2 = 0
    if type(text2) is str:
        textwords2 = cleansubmtext(text2).split(' ')
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
    else:
        match = 0
    return match