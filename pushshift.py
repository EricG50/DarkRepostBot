import praw
import requests
import json

def getPushshiftData(sub=None, before=None, after=None, ids=None):
    suffix=''
    searchType = 'submission'
    if (before is not None):
        suffix += '&before='+str(before)
    if (after is not None):
        suffix += '&after='+str(after)
    if (sub is not None):
        suffix += '&subreddit='+sub
    if (ids is not None):
        suffix += '&ids='+','.join(ids)

    url = 'https://api.pushshift.io/reddit/search/'+searchType+'?sort=asc&sort_type=created_utc&size=1000'+suffix
    print('loading '+url)
    r = requests.get(url)
    #with open('data.json', 'wb') as w:
    #w.write(r.content)
    data = json.loads(r.content)
    if len(data['data']) > 0:
        prev_end_date = data['data'][-1]['created_utc']
    else:
        prev_end_date = None
    return (data, prev_end_date)

def getPosts(posts):
    postslist = []
    for post in posts:
        postslist.append(post['id'])
    return postslist
