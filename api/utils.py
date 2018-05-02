import os
import aiohttp

PBRAIN_SCHEDULER_ADDRESS = os.environ.get('PBRAIN_SCHEDULER_ADDRESS', None)
APP_ADDRESS = os.environ.get('MOCK_ADDRESS', 'mock:8000')


async def async_post(url, data=None, json=None):
    async with aiohttp.ClientSession() as session:
        async with session.post(url, data=data, json=json) as resp:
            status = resp.status
            text = resp.text()
    text_done = await text
    print('response:')
    print('\tstatus:', status)
    print('\tbody:', text_done)


async def async_get(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            status = resp.status
            text = resp.text()
    print('local response:')
    print('\tstatus:', status)
    text_done = await text
    print('\tbody:', text_done)
