import json
import asyncio
import aiohttp
import aioredis
import uuid

from distributed import Client
import taxcalc
from tornado.web import RequestHandler
from tornado.ioloop import IOLoop

from utils import (PBRAIN_SCHEDULER_ADDRESS, APP_ADDRESS, REDIS_ADDRESS,
                   QUEUING, PENDING, SUCCESS, FAIL, RedisConnection)


def from_json(keywords):
    keys = keywords.keys()
    for k in keys:
        keywords[int(k)] = keywords.pop(k)
    return keywords

taxcalc.tbi.from_json = from_json


async def calc(future, policy_dict, job_id):
    """
    Run one Tax-Calculator reform with small sample to demonstrate use of
    dask + async on a simplified version of a PolicyBrain worker
    """

    kw = {
        'start_year': 2018,
        'use_full_sample': False,
        'user_mods': {
            u'policy': policy_dict,
            u'growdiff_response': {},
            u'behavior': {},
            u'consumption': {},
            u'growdiff_baseline': {}
        },
        'year_n': 0,
        'use_puf_not_cps': False,
        'return_dict': True
    }
    # this will have to be initialized elsewhere but works for demo purposes
    print('getting client at address', PBRAIN_SCHEDULER_ADDRESS)
    client = await Client(PBRAIN_SCHEDULER_ADDRESS, asynchronous=True)
    print('calc client', client)
    print('calc sched info', client._scheduler_identity)
    print('submit kw...', json.dumps(kw, indent=3))

    async with RedisConnection(REDIS_ADDRESS,
                               loop=IOLoop.current().asyncio_loop,
                               encoding='utf-8') as conn:
        job_status = {'status': PENDING, 'result': False}
        ok = await conn.execute('set', job_id, json.dumps(job_status))
        assert ok == 'OK', ok

        # returns a new future for the dask job
        dask_futures = []
        for i in range(0, 2):
            kw['year_n'] = i
            dask_futures.append(
                client.submit(taxcalc.tbi.run_nth_year_tax_calc_model, **kw)
            )
        # use await here -->
        # 1. control is passed back to the event main loop
        # 2. dask is pushing this job onto the compute cluster
        print('await on result...')
        results = await client.gather(dask_futures)
        await client.close()
        aggr_d = {}
        for result in results:
            aggr_d.update(result['aggr_d'])
    print('got aggr_d', aggr_d)
    # store results in redis server
    async with RedisConnection(REDIS_ADDRESS,
                               loop=IOLoop.current().asyncio_loop,
                               encoding='utf-8') as conn:
        print('setting result at redis server')
        job_status = {'status': SUCCESS, 'result': aggr_d}
        ok = await conn.execute('set', job_id, json.dumps(job_status))
    assert ok == 'OK', ok
    print('done with job', job_id)
    # set result on future
    future.set_result(True)


class TaxBrainHandler(RequestHandler):

    # async def get(self):
    #     print('GET')
    #     client = await Client(PBRAIN_SCHEDULER_ADDRESS, asynchronous=True)
    #     result = await client.processing()
    #     print(result)
    #     for address in result:
    #         print('checking jobs at address:', address)
    #         for job in result[address]:
    #             print('\t', job)
    #
    #     self.write(json.dumps(result))

    async def get(self):
        print('GET-Check status')
        job_id = self.get_query_argument('job_id', False)
        if not job_id:
            self.write('you must send a job_id for look-up')
        async with RedisConnection(REDIS_ADDRESS,
                                   loop=IOLoop.current().asyncio_loop,
                                   encoding='utf-8') as conn:

            print('got job_id', job_id)
            _result = await conn.execute('get', job_id)
        # result = json.loads(_result)
        print('result', _result)
        if _result is None:
            print(f'look-up failed for id {job_id}')
            self.write({'status': [f'look-up failed for id {job_id}']})
        else:
            self.write(_result)

    async def post(self):
        """
        POST end point for dask api. This is the gateway to submitting jobs
        on the PolicyBrain dask clusterself.

        For demo purposes, this only works with a subset of the arguments
        that can be passed to taxcalc--the static reform parameters.
        You can test this out by running:
        http -f POST http://localhost:8888/taxcalc policy='{"2018": {"_II_em": [8000]}}'

        This creates an `asyncio.Future` object and schedules it for future
        completion with the `ensure_future` function.
        """
        print('POST')
        # get the POST data and do some parsing
        print('body', self.request.body)
        keywords = json.loads(self.request.body.decode('utf-8'))
        print('raw policy data', keywords)
        function_args = taxcalc.tbi.from_json(keywords['keywords'])
        print('got function_args', function_args)
        # create future, schedule the execution of coroutine `calc`
        loop = IOLoop.current()
        print('loop', loop, dir(loop))
        job_id = str(uuid.uuid4())
        async with RedisConnection(REDIS_ADDRESS,
                                   loop=IOLoop.current().asyncio_loop,
                                   encoding='utf-8') as conn:
            job_status = {'status': QUEUING, 'result': False}
            ok = await conn.execute('set', job_id, json.dumps(job_status))
            assert ok == 'OK', ok

        future = asyncio.Future()
        asyncio.ensure_future(calc(future, function_args, job_id))

        job_status['job_id'] = job_id
        self.write(job_status)
