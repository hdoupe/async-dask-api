import falcon
import json

class Result(object):

    def on_get(self, req, resp):
        print(req)
        resp.status = falcon.HTTP_200
        resp.body = 'We successfully received your request\n'

    def on_post(self, req, resp):
        raw_json = req.stream.read()
        result = raw_json.decode('utf-8')
        print('got a result', result)

        resp.body = result
        resp.status = falcon.HTTP_OK


class Healthy(object):
    def on_get(self, req, resp):
        print('GET-HEALTHY-READY')
        resp.body = 'feeling healthy...'

api = application = falcon.API()
result = Result()
healthy = Healthy()
api.add_route('/result', result)
api.add_route('/healthy', healthy)
