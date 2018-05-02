import json
import asyncio
import aiohttp

from distributed import Client
import taxcalc
from tornado.web import RequestHandler

from utils import PBRAIN_SCHEDULER_ADDRESS, APP_ADDRESS, async_post, async_get


def from_json(keywords):
    keys = keywords.keys()
    for k in keys:
        keywords[int(k)] = keywords.pop(k)
    return keywords

taxcalc.tbi.from_json = from_json


async def calc(future, policy_dict):
    """
    Run one Tax-Calculator reform with small sample to demonstrate use of
    dask + async on a simplified version of a PolicyBrain worker
    """

    kw = {
        'start_year': 2018,
        'use_full_sample': True,
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
    # returns a new future for the dask job
    dask_futures = []
    for i in range(0, 6):
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
    print('posting result to', f'http://{APP_ADDRESS}/result')

    # posts result to falcon app in mock_pb.py
    await async_post(
        f'http://{APP_ADDRESS}/result',
        json=json.dumps({'aggr_d': aggr_d})
    )
    print('finished. setting result...')
    # set result on future
    future.set_result('DONE')


class TaxBrainHandler(RequestHandler):

    async def get(self):
        print('GET')
        client = await Client(PBRAIN_SCHEDULER_ADDRESS, asynchronous=True)
        result = await client.processing()
        print(result)
        for address in result:
            print('checking jobs at address:', address)
            for job in result[address]:
                print('\t', job)

        self.write(json.dumps(result))

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
        print('body', self.request.body)
        keywords = json.loads(self.request.body.decode('utf-8'))
        print('raw policy data', keywords)
        function_args = taxcalc.tbi.from_json(keywords['keywords'])
        print('got function_args', function_args)
        # create future, schedule the execution of coroutine `calc`
        future = asyncio.Future()
        asyncio.ensure_future(calc(future, function_args))
        body = (
            'a future has been scheduled, the model is running, a result \n'
            'will be returned soon'
        )
        self.write(body)
