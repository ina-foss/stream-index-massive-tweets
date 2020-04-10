import argparse
import json
from flask import Flask, Response, request
import logging

from thread import StreamThread, e
from config import ACCESS

s = None
app = Flask(__name__)


@app.route('/stream', methods=['POST'])
def update_track():
    """ Send stream job to streamer with arguments contained in request.json
    """
    global s
    if s is not None:
        disconnect()
    s = StreamThread(args.key, args.rabbit_host, args.rabbit_port, **request.json)
    s.start()
    return Response(status=200)


@app.route('/disconnect')
def disconnect():
    """ Send instruction to disconnect from Twitter API to streamer
    """
    global s
    if s is not None:
        s.twitter.do_continue = False
        s.join()
        e.clear()
        s = None
        return Response(response="disconnected", status=200)
    return Response(status=501)


@app.route('/')
def info():
    """ Get streamer key, i.e. the OAuth  authentication key that was attributed to this streamer, and the current
    job executed by this streamer
    """
    if s is None:
        res = {"key": args.key}
    else:
        res = {"key": args.key, "track": s.track, "lang": s.lang}
    return Response(response=json.dumps(res), status=200, mimetype="application/json")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', required=True, help='Path to tweets storage folder')
    parser.add_argument('--key', required=False, default=0, type=int, choices=range(len(ACCESS)),
                        help='Index of Twitter  authentication key (from 0 to %d)' % len(ACCESS))
    parser.add_argument('--es_host', required=False, default="elasticsearch", help='Host of elasticsearch database')
    parser.add_argument('--es_port', required=False, default=9200, help='Port of elasticsearch database')
    parser.add_argument('--rabbit_host', required=False, default="rabbitmq", help='RabbitMQ host')
    parser.add_argument('--rabbit_port', required=False, default=5672, help='RabbitMQ port')

    args = parser.parse_args()

    logging.basicConfig(format='%(asctime)s - %(levelname)s : %(message)s', level=logging.INFO)


    app.run(host='0.0.0.0', ssl_context=None, debug=False)




