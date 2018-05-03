import time
import requests
import json

IP = 'localhost:8888'
s = time.time()
resp = requests.post(f'http://{IP}/taxbrain/', data='{"keywords": {"2018": {"_II_em": [8015]}}}')
f = time.time()
t = f - s
print(resp.text)
status = resp.json()
print(f'got post status {t}s', status)
job_id = status['job_id']

while status['status'] not in ('success', 'fail'):
    s = time.time()
    resp = requests.get(f'http://{IP}/taxbrain/?job_id={job_id}')
    f = time.time()
    t = f - s
    try:
        status = resp.json()
    except json.decoder.JSONDecodeError as e:
        print(e)
        print('error but got response', resp.text)
        continue

    print(f'resp status {t}s', status)
    print('\n\n')
    time.sleep(0.1)
