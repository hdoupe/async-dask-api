import asyncio
import random
import json
import time

from tornado.testing import AsyncHTTPTestCase, AsyncTestCase
from distributed import Client
# from distributed.utils_test import loop
import taxcalc

from api.cluster_api import make_app
from api.utils import SUCCESS, FAIL


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
        response = self.fetch('/ready')
        assert response.code == 200
        assert response.body == b'feeling ready...'


class TaxBrainTestCase(AsyncHTTPTestCase):

    def get_app(self):
        return make_app()

    def test_post_job_and_polling(self):
        from api.taxbrain import taxcalc
        def f(**kwargs):
            print(kwargs)
            time.sleep(0.5)
            return {'aggr_d': {'result': kwargs['year_n']}}
        real_run = taxcalc.tbi.run_nth_year_tax_calc_model
        taxcalc.tbi.run_nth_year_tax_calc_model = f
        try:
            headers = {'Content-Type': 'application/json'}
            body = {"keywords": {"2018": {"_II_em": [8000]}}}
            response = self.fetch(
                '/taxbrain/',
                method='POST',
                headers=headers,
                body=json.dumps(body).encode('utf-8'),
            )
            print(response.error)
            assert response.code == 200
            status = json.loads(response.body.decode('utf-8'))
            job_id = status['job_id']
            print('init status', status)
            while status['status'] not in (SUCCESS, FAIL):
                response = self.fetch(f'/taxbrain/?job_id={job_id}')
                status = json.loads(response.body.decode('utf-8'))
                print('status', status)
                time.sleep(2)

            assert status['status'] == SUCCESS
            assert status['result'] != False

        finally:
            taxcalc.tbi.run_nth_year_tax_calc_model = real_run

    def test_post_failed_job(self):
        from api.taxbrain import taxcalc
        def f(**kwargs):
            print(kwargs)
            time.sleep(0.5)
            if kwargs['year_n'] == 0:
                raise ValueError('Simulate Failed job')
            return {'aggr_d': {'result': kwargs['year_n']}}
        real_run = taxcalc.tbi.run_nth_year_tax_calc_model
        taxcalc.tbi.run_nth_year_tax_calc_model = f
        try:
            headers = {'Content-Type': 'application/json'}
            body = {"keywords": {"2018": {"_II_em": [8000]}}}
            response = self.fetch(
                '/taxbrain/',
                method='POST',
                headers=headers,
                body=json.dumps(body).encode('utf-8'),
            )
            print(response.error)
            assert response.code == 200
            status = json.loads(response.body.decode('utf-8'))
            job_id = status['job_id']
            print('init status', status)
            tries = 5
            while status['status'] not in (SUCCESS, FAIL) and tries > 0:
                response = self.fetch(f'/taxbrain/?job_id={job_id}')
                status = json.loads(response.body.decode('utf-8'))
                print('status', status)
                time.sleep(2)
                tries -= 1

            assert status['status'] == FAIL
            assert status['result'] != False

        finally:
            taxcalc.tbi.run_nth_year_tax_calc_model = real_run
