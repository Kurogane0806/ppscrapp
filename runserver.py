from tornado.wsgi import WSGIContainer
from tornado.httpserver import HTTPServer
from tornado.ioloop import IOLoop
from server import app
import tornado.log

tornado.log.enable_pretty_logging()
http_server = HTTPServer(WSGIContainer(app))
http_server.listen(8080)
IOLoop.instance().start()
