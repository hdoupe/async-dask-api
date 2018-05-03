import os

PBRAIN_SCHEDULER_ADDRESS = os.environ.get('PBRAIN_SCHEDULER_ADDRESS', None)
APP_ADDRESS = os.environ.get('MOCK_ADDRESS', 'mock:8000')
REDIS_ADDRESS = os.environ.get('REDIS_ADDRESS', 'redis://localhost:6379')

QUEUING = 'queuing'
PENDING = 'pending'
SUCCESS = 'success'
FAIL = 'fail'
