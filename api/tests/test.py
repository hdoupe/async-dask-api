import asyncio
import random
import json

from tornado.testing import AsyncHTTPTestCase, AsyncTestCase
from distributed import Client
# from distributed.utils_test import loop
import taxcalc

from api.api import make_app


async def mock_aiohttp(url, data=None, json=None):
    await asyncio.sleep(0.5)


class APITestCase(AsyncHTTPTestCase):

    def get_app(self):
        return make_app()

    def test_healthy(self):
        response = self.fetch('/healthy')
        assert response.code == 200
        assert response.body == b'feeling healthy...'

    def test_ready(self):
        from api import utils
        real_get = utils.async_get
        utils.async_get = mock_aiohttp
        try:
            response = self.fetch('/ready')
            assert response.code == 200
            assert response.body == b'feeling ready...'
        finally:
            utils.async_get = real_get


class TaxBrainTestCase(AsyncHTTPTestCase):

    def get_app(self):
        return make_app()

    def test_post(self):
        from taxcalc import tbi
        def f(**kwargs):
            print(kwargs)
            time.sleep(int(random.random() * 10))
            return {'aggr_d': {'result': kwargs['year_n']}}
        real_run = tbi.run_nth_year_tax_calc_model
        tbi.run_nth_year_tax_calc_model = f
        try:
            headers = {'Content-Type': 'application/json'}
            body = {'keywords': '{"2018": {"_II_em": [8000]}}'}
            response = self.fetch(
                '/taxbrain',
                method='POST',
                headers=headers,
                body=json.dumps(body).encode('utf-8'),
            )
            print(response.error)
            assert response.code == 200
            pending = asyncio.Task.all_tasks()
            print('pending', pending)
            # yield from asyncio.gather(*pending)
            client = Client()
            print('client', client.has_what())
            # assert response.body == b'feeling healthy...'
        finally:
            tbi.run_nth_year_tax_calc_model = real_run
