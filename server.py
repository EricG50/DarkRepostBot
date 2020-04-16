import routes
import threading
import json
from log import *
from http.server import BaseHTTPRequestHandler,HTTPServer

class PostHanlder():
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

        path = self.path.lower().replace('/', '')
        if not hasattr(ph, path):
            self.invalid_route()
            return

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
        self.server = HTTPServer(('', kwargs.get('port', 80)), Handler)
        self.servThread = threading.Thread(target=self.serve)
        self.servThread.start()
    def serve(self):
        print('Server started on port ' + str(self.server.server_port))
        self.server.serve_forever()
