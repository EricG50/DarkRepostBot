import os.path
import json
import hashlib
import string
import random
from log import *
from http.server import BaseHTTPRequestHandler

def respond(h, code):
    h.send_response(code)

def hash(text : str) -> str:
    m = hashlib.sha256()
    m.update(text.encode('utf-8'))
    return m.hexdigest()

def generateKey(size=10, chars=string.ascii_lowercase + string.digits):
    return ''.join(random.choice(chars) for _ in range(size))

def GET(h):
    h.send_header("Content-type", "text/html")
    respond(h, 200)
    with open('www/index.html', 'rb') as f:
        h.wfile.write(f.read())

def GETauth(h):
    content_len = int(h.headers.get('Content-Length'))
    bodytext = h.rfile.read(content_len)
    body = json.loads(bodytext)
    if 'user' not in body or 'password' not in body:
        respond(h, 400)
        h.end_headers()
    logp(f"Auth request IP: {h.client_address[0]} user: {body['user']} password: {body['password']}")
    with open('users.json', 'r') as f:
        users = json.load(f)
    for user in users['users']:
        if user['name'] == body['user'] and user['password'] == hash(body['password']):
            key = generateKey()
            h.whitelist.append({ 'ip': h.client_address[0], 'name': user['name'], 'key': key, 'permissions': user['permissions']})
            respond(h, 200)
            h.send_header("Content-type", "text/plain")
            h.end_headers()
            h.wfile.write(key.encode('utf-8'))
            logp('Request aproved key: ' + key)
            return
    logp('Request rejected')
    respond(h, 403)

def GETerrors(h):
    respond(h, 200)
    h.send_header("Content-type", "text/plain")
    h.end_headers()
    with open('err.txt', 'rb') as f:
        h.wfile.write(f.read())

def GETplog(h):
    respond(h, 200)
    h.send_header("Content-type", "text/json")
    h.end_headers()
    with open('procplog.json', 'rb') as f:
        h.wfile.write(f.read())

def GETstats(h):
    respond(h, 200)
    h.send_header("Content-type", "text/json")
    h.end_headers()
    with open('stats.json', 'rb') as f:
        h.wfile.write(f.read())