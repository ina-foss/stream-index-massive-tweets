import requests
import logging
import time

logging.basicConfig(format='%(asctime)s - %(levelname)s : %(message)s', level=logging.INFO)


def stream():
    """
    Send stream instructions to streamer servers in the form of HTTP POST requests.
    The streamer_0 is dedicated to the Twitter sample API, so we don't send any keywords or language to track
    """
    logging.info("'http://streamer_0:5000/stream")
    r = requests.post("http://streamer_0:5000/stream", json={})
    logging.info("'http://streamer_0:5000/stream', response = %s" % r.status_code)
    if r.status_code != 200:
        time.sleep(2)
        stream()


if __name__ == "__main__":
    while True:
        stream()
        time.sleep(3600 * 24)
