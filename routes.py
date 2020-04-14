import os.path
from http.server import BaseHTTPRequestHandler

def GET(h : BaseHTTPRequestHandler):
    h.send_response(200)
    h.send_header("Content-type", "text/html")
    h.end_headers()
    h.wfile.write('Hello world'.encode('utf-8'))

def GETerrors(h : BaseHTTPRequestHandler):
    h.send_response(200)
    h.send_header("Content-type", "text/plain")
    h.end_headers()
    with open('err.txt', 'rb') as f:
        h.wfile.write(f.read())

def GETplog(h : BaseHTTPRequestHandler):
    h.send_response(200)
    h.send_header("Content-type", "text/json")
    h.end_headers()
    with open('procplog.json', 'rb') as f:
        h.wfile.write(f.read())

def GETstats(h : BaseHTTPRequestHandler):
    h.send_response(200)
    h.send_header("Content-type", "text/json")
    h.end_headers()
    with open('stats.json', 'rb') as f:
        h.wfile.write(f.read())