import time
import requests
import logging
from config import KEYWORDS, LANG

logging.basicConfig(format='%(asctime)s - %(levelname)s : %(message)s', level=logging.INFO)


def stream():
    """
    Send stream instructions from config file to streamer servers in the form of HTTP POST requests.
    """
    for i, words in enumerate(KEYWORDS):
        while True:
            try:
                r = requests.post("http://streamer_{}:5000/stream".format(i+1),
                              json={"lang": LANG, "tag": words["tag"], "track": words["track"].split()})
                break
            except requests.exceptions.ConnectionError:
                logging.error("Could not connect to server streamer_{}, retrying".format(i+1))
                time.sleep(2)
                continue
        logging.info("'http://streamer_{}:5000/stream', response = {}".format(i+1, r.status_code))
        if r.status_code != 200:
            time.sleep(2)
            stream()


if __name__ == "__main__":
    while True:
        stream()
        time.sleep(3600*24)
