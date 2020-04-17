import routes
import threading
import json
from log import *
from http.server import BaseHTTPRequestHandler,HTTPServer
import sys
import os
import time

class PostHanlder():
    @classmethod
    def closeserver(cls):
        time.sleep(15)
        Server.server.shutdown()

    def setMethods(self, kwargs):
        self.repfalsepos = kwargs.get('repfalsepos', None)

    def handle(self, path, h, body):
        getattr(self, path)(h, body)

    def repfalsepos(self, h, body):
        if 'id' not in body:
            h.send_response(400)
            h.end_headers()
            return
        response = self.repfalsepos(body)
        h.send_response(response)
        h.end_headers()

    def unauth(self, h, body):
        for i, user in enumerate(h.whitelist):
            if user['ip'] == h.client_address[0] and user['key'] == body['key']:
                del[h.whitelist[i]]
                logp(f"User {user['name']} IP:{user['ip']} logged out")
                h.send_response(200)
                h.end_headers()
    
    def shutdown(self, h, body):
        force = body.get('force', False)
        logp(f"Recieved shutdown request from user {body['sender']} reason: {body.get('reason')} force: {str(force)}")
        h.send_response(200)
        h.end_headers()
        if force:
            os._exit(1)
        else:
            threading.Thread(target=self.closeserver).start()
        
ph = PostHanlder()

class Handler(BaseHTTPRequestHandler):
    whitelist = []
    running = True
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
        path = self.path.lower().replace('/', '')
        if not hasattr(ph, path):
            self.invalid_route()
            return

        content_len = int(self.headers.get('Content-Length', 0))
        if content_len == 0:
            self.send_response(400)
            self.end_headers()
            return
        bodytext = self.rfile.read(content_len)
        body = json.loads(bodytext)

        if 'key' not in body:
            self.send_response(400)
            self.end_headers()
            return
        
        for user in self.whitelist:
            if user['ip'] == self.client_address[0] and user['key'] == body['key']:
                body['sender'] = user['name']
                if user['permissions'] == 'all' or path in user['permissions']:
                    try:
                        ph.handle(path, self, body)
                    except Exception as e:
                        self.servererror(str(e))
                else:
                    self.send_response(401)
                    self.end_headers()
                return
        self.send_response(403)
        self.end_headers()

    def servererror(self, message):
        ErrLog.log(message, 5)
        self.send_response(500, message)
        self.end_headers()
    def invalid_route(self):
        self.send_response(404, 'Not found')
        self.end_headers()

class Server:
    @classmethod
    def start(cls, **kwargs):
        ph.setMethods(kwargs)
        cls.server = HTTPServer(('', kwargs.get('port', 80)), Handler)
        cls.servThread = threading.Thread(target=cls.serve)
        cls.servThread.start()
    @classmethod
    def waitforexit(cls):
        cls.servThread.join()
    @classmethod
    def exit(cls):
        cls.server.shutdown()
    @classmethod
    def serve(cls):
        logp('Server started on port ' + str(cls.server.server_port))
        cls.server.serve_forever()
        logp('Server stopped')
