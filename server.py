import routes
import threading
from http.server import BaseHTTPRequestHandler,HTTPServer

class PostHanlder():
    def setMethods(self, **kwargs):
        self.reportfalsepositive = kwargs.get('repFalsePos')
    def handle(self, h):
        if h.path=='/repFalsePos':
            self.reportfalsepositive(h)

class Handler(BaseHTTPRequestHandler):
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
        ph.handle(self)

    def servererror(self):
        self.send_response(500)
    def invalid_route(self):
        self.send_response(404)

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
