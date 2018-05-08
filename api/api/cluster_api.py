from tornado.web import Application, RequestHandler
from tornado.ioloop import IOLoop
from distributed import Client

from api.taxbrain import TaxBrainHandler
from api.utils import (PBRAIN_SCHEDULER_ADDRESS, REDIS_ADDRESS,
                       RedisConnection)

class Ready(RequestHandler):

    async def get(self):
        print('GET-READY')
        client = await Client(PBRAIN_SCHEDULER_ADDRESS, asynchronous=True)
        print('client', client)
        print('sched info', client._scheduler_identity)
        print('closing client')
        await client.close()
        print('make sure redis is reachable')
        async with RedisConnection(REDIS_ADDRESS,
                                   loop=IOLoop.current().asyncio_loop,
                                   encoding='utf-8') as conn:
            assert conn is not None

        self.write('feeling ready...')


class Healthy(RequestHandler):

    async def get(self):
        print('GET-HEALTH')

        self.write('feeling healthy...')


def make_app():
    return Application(
        [(r'/taxbrain/', TaxBrainHandler),
         (r'/ready', Ready),
         (r'/healthy', Healthy)],
        default_host='0.0.0.0',
        debug=True,
        autoreload=True
    )

if __name__ == "__main__":
    print('starting up app...')
    app = make_app()
    app.listen(8888)
    IOLoop.current().start()
