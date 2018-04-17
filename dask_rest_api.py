import json
import asyncio

import aiohttp

import tornado.ioloop
import tornado.web
from dask.distributed import Client

import taxcalc


async def calc(future, policy_dict):
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
    # also maybe AioClient should be used instead of regular client
    # depends on which event loop is being used: asyncio loop or tornado loop
    # http://distributed.readthedocs.io/en/latest/asynchronous.html#asyncio
    client = await Client(asynchronous=True)
    print('submit kw...', json.dumps(kw, indent=3))
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
    aggr_d = {}
    for result in results:
        aggr_d.update(result['aggr_d'])
    print('got aggr_d', aggr_d)
    print('posting result...')
    # posts result to falcon app in mock_pb.py
    # async with aiohttp.ClientSession() as session:
    #     async with session.post('http://mock:8000/result', json=json.dumps({'aggr_d': aggr_d})) as resp:
    #         status = resp.status
    #         text = resp.text()
    # print('local response:')
    # print('\tstatus:', status)
    # text_done = await text
    # print('\tbody:', text_done)
    print('finished. setting result...')
    # set result on future created in `post` to be retrieved in the later
    future.set_result('DONE')


class MainHandler(tornado.web.RequestHandler):

    def get(self):
        print('GET')
        self.write('get does not do anything')

    def post(self):
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
        policy = self.get_body_argument('policy')
        print('raw policy data', policy)
        policy_dict = json.loads(policy)
        keys = policy_dict.keys()
        for k in keys:
            policy_dict[int(k)] = policy_dict.pop(k)
        print('got policy_dict', policy_dict)
        # create future, schedule the execution of coroutine `calc`
        # `calc_callback` is the callback funcion i.e. the function called once
        # `calc` is done
        future = asyncio.Future()
        asyncio.ensure_future(calc(future, policy_dict))
        body = (
            'a future has been scheduled, the model is running, a result \n'
            'will be returned soon'
        )
        self.write(body)


class Ready(tornado.web.RequestHandler):

    async def get(self):
        print('GET-READY')
        client = await Client(asynchronous=True)
        print('client', client)
        print('sched info', client._scheduler_identity)

        self.write('feeling ready...')

class Healthy(tornado.web.RequestHandler):

    async def get(self):
        print('GET-HEALTH')

        self.write('feeling healthy...')


def make_app():
    return tornado.web.Application(
        [(r'/taxcalc', MainHandler),
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
    tornado.ioloop.IOLoop.current().start()
