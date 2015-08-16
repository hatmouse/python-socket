__author__ = 'jmpews'

import tornado.web
import tornado.ioloop
import tornado.gen


class MainHandler(tornado.web.RequestHandler):
    @tornado.web.asynchronous
    @tornado.gen.coroutine
    def get(self, *args, **kwargs):
        yield tornado.gen.sleep(10)
        self.write('hello world...')

application=tornado.web.Application([
    (r'/',MainHandler)
])

application.listen(7777)
print('listening 7777...')
tornado.ioloop.IOLoop.current().start()