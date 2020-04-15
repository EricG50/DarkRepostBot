import routes
import threading
import json
from http.server import BaseHTTPRequestHandler,HTTPServer

class PostHanlder():
    def setMethods(self, **kwargs):
        self.reportfalsepositive = kwargs.get('repFalsePos', None)
    def handle(self, h):
        if h.path=='/repFalsePos':
            content_len = int(h.headers.get('Content-Length'))
            bodytext = h.rfile.read(content_len)
            body = json.loads(bodytext)
            response = self.reportfalsepositive(body['id'], body.get('message', ''))
            h.send_response(response)
            h.end_headers()

class Handler(BaseHTTPRequestHandler):
    whitelist = [ '89.136.19.1' ]
    def do_GET(self):
        routename = 'GET' + self.path.lower().replace('/', '')
        try:
            route = getattr(routes, routename)
            route(self)
        except AttributeError:
            self.invalid_route()
        except:
            self.servererror()
        
    def do_POST(self):
        if self.client_address[0] not in self.whitelist:
            self.send_response(403)
            self.end_headers()
        try:
            ph.handle(self)
        except Exception as e:
            self.servererror(str(e))


    def servererror(self, message):
        self.send_response(500, message)
        self.end_headers()
    def invalid_route(self):
        self.send_response(404)
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
