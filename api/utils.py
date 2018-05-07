import os

import aioredis

PBRAIN_SCHEDULER_ADDRESS = os.environ.get('PBRAIN_SCHEDULER_ADDRESS', None)
APP_ADDRESS = os.environ.get('MOCK_ADDRESS', 'mock:8000')
REDIS_ADDRESS = os.environ.get('REDIS_ADDRESS', 'redis://localhost:6379')

QUEUING = 'queuing'
PENDING = 'pending'
SUCCESS = 'success'
FAIL = 'fail'


# waiting on python 3.7
# @asynccontextmanager
# async def redis_connection(address, loop, encoding=None):
#     conn = await aioredis.create_connection(address, loop=loop,
#                                             encoding=encoding)
#     try:
#         yield conn
#     finally:
#         conn.close()
#         await conn.wait_closed()


class RedisConnection():
    def __init__(self, address, loop, encoding):
        self.address = address
        self.loop = loop
        self.encoding = encoding

    async def __aenter__(self):
        self.conn = await aioredis.create_connection(self.address,
                                                     loop=self.loop,
                                                     encoding=self.encoding)
        return self.conn

    async def __aexit__(self, exc_type, exc, tb):
        self.conn.close()
        await self.conn.wait_closed()
