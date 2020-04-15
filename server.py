import routes
import threading
import json
from log import *
from http.server import BaseHTTPRequestHandler,HTTPServer

class PostHanlder():
    def setMethods(self, kwargs):
        self.reportfalsepositive = kwargs.get('repFalsePos', None)
    def handle(self, h, body):
        if h.path=='/repfalsepos':
            if 'id' not in body:
                h.send_response(400)
                h.end_headers()
                return
            response = self.reportfalsepositive(body['id'], body.get('message', ''))
            h.send_response(response)
            h.end_headers()
        else:
            self.send_response(404, 'Not found')
            self.end_headers()

class Handler(BaseHTTPRequestHandler):
    whitelist = []
    def do_GET(self):
        routename = 'GET' + self.path.lower().replace('/', '')
        try:
            route = getattr(routes, routename)
        except AttributeError:
            self.invalid_route()
            return
        try:
            route(self)
        except Exception as e:
            self.servererror('Server error:' +  str(e))
        
    def do_POST(self):
        content_len = int(self.headers.get('Content-Length'))
        bodytext = self.rfile.read(content_len)
        body = json.loads(bodytext)

        if 'key' not in body:
            self.send_response(400)
            self.end_headers()
            return
        for user in self.whitelist:
            if user['ip'] == self.client_address[0] and user['key'] == body['key']:
                try:
                    ph.handle(self, body)
                except Exception as e:
                    self.servererror(str(e))
                return
        self.send_response(403)
        self.end_headers()

    def servererror(self, message):
        logerror(message)
        self.send_response(500, message)
        self.end_headers()
    def invalid_route(self):
        self.send_response(404, 'Not found')
        self.end_headers()

ph = PostHanlder()

class Server:
    def __init__(self, **kwargs):
        ph.setMethods(kwargs)
        self.server = HTTPServer(('localhost', kwargs.get('port', 80)), Handler)
        self.servThread = threading.Thread(target=self.serve)
        self.servThread.start()
    def serve(self):
        print('Server started on port ' + str(self.server.server_port))
        self.server.serve_forever()
