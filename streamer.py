# -*- coding: utf-8 -*-
import time
import json
import requests
import logging
import pika

from config import PROXY
from twython import TwythonStreamer

logging.basicConfig(format='%(asctime)s - %(levelname)s : %(message)s', level=logging.INFO)


class sampleStreamer(TwythonStreamer):
    """
    Retrieve data from the Twitter Streaming API.

    The streaming API requires
    `OAuth 1.0 <http://en.wikipedia.org/wiki/OAuth>`_ authentication.
    """

    def __init__(self, rabbit_host, rabbit_port, app_key, app_secret, oauth_token, oauth_token_secret, tag):
        """Create a new instance of the sampleStreamer class that will connect to Twitter API and send tweets
        to rabbitmq queue using pika module.
        :param str app_key, app_secret, oauth_token, oauth_token_secret: credentials for Twitter API authentication
        :param str tag: a tag that will be added to the tweet body to indicate its collection method

        """
        self.rabbit_host = rabbit_host
        self.rabbit_port = rabbit_port
        self.rabbit_client = self.open_rabbit_connection()
        self.tweets_queue = self.open_rabbit_channel()
        if PROXY:
            client_args = {
                'proxies': PROXY
            }
        else:
            client_args = {}
        self.do_continue = True
        TwythonStreamer.__init__(self, app_key, app_secret, oauth_token,
                                 oauth_token_secret, timeout=100, chunk_size=200, client_args=client_args)
        self.tag = tag

    def open_rabbit_connection(self):
        for i in range(3):
            try:
                rabbit_client = pika.BlockingConnection(
                    pika.ConnectionParameters(host=self.rabbit_host, port=self.rabbit_port,
                                              # connection_attempts=1000, retry_delay=1,
                                              # blocked_connection_timeout=1000,
                                              # socket_timeout=1000,
                                              ssl=False,
                                              credentials=pika.credentials.PlainCredentials(
                                                  username='user',
                                                  password='password')))
                break
            except pika.exceptions.AMQPConnectionError:
                logging.error("pika AMQPConnectionError, retrying")
            except Exception as error:
                logging.error("other error, retrying " + str(error))

        return rabbit_client

    def open_rabbit_channel(self):
        tweets_queue = self.rabbit_client.channel()
        tweets_queue.queue_declare(queue='tweets')
        return tweets_queue

    def on_success(self, data):
        """
        :param data: response from Twitter API
        """
        data["tags"] = [self.tag]
        data["events"] = [""]
        try:
            self.tweets_queue.basic_publish(exchange='',
                                            routing_key='tweets',
                                            body=json.dumps(data))
        except pika.exceptions.AMQPConnectionError:
            logging.error("AMQPConnectionError, trying to reconnect")
            self.rabbit_client = self.open_rabbit_connection()
            self.tweets_queue = self.open_rabbit_channel()
            self.on_success(data)

        if self.do_continue == False:
            print("disconnect")
            self.disconnect()

    def on_error(self, status_code, data):
        """
        :param status_code: The status code returned by the Twitter API
        :param data: The response from Twitter API

        """
        print(status_code)
        print(data)

    def sample(self, lang=None):
        """
        Wrapper for 'statuses / sample' API call
        """
        while self.do_continue:

            # Stream in an endless loop until limit is reached. See twython
            # issue 288: https://github.com/ryanmcgrath/twython/issues/288

            try:
                self.statuses.sample(language=lang)
            except requests.exceptions.ChunkedEncodingError as e:
                if e is not None:
                    print("Error (stream will continue): {0}".format(e))

    def filter(self, track='', lang='fr'):
        """
        Wrapper for 'statuses / filter' API call
        """

        while self.do_continue:
            # Stream in an endless loop until limit is reached
            try:
                self.statuses.filter(track=track, language=lang)
            except requests.exceptions.ChunkedEncodingError as e:
                if e is not None:
                    print("Error (stream will continue): {0}".format(e))
                continue
            except requests.exceptions.ConnectionError as error:
                logging.error(str(error) + " sleep 5 sec")
                time.sleep(5)
                continue
