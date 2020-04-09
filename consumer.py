# -*- coding: utf-8 -*-
import argparse
import logging
import pika
import threading
import gzip
import json
import time
import os
import socket
from datetime import datetime
from indexer import TweetsIndex
from config import FILEBREAK

LOCK = threading.Lock()


class Consumer(object):
    """This is an example consumer that will handle unexpected interactions
    with RabbitMQ such as channel and connection closures.

    If RabbitMQ closes the connection, it will reopen it. You should
    look at the output, as there are limited reasons why the connection may
    be closed, which usually are tied to permission related issues or
    socket timeouts.

    If the channel is closed, it will indicate a problem with one of the
    commands that were issued and that should surface in the output as well.

    """
    PREFETCH_COUNT = 1600
    EXCHANGE = 'message'
    EXCHANGE_TYPE = 'topic'
    ROUTING_KEY = 'example.text'

    def __init__(self, channel_name, parameters):
        """Create a new instance of the consumer class, passing in the AMQP
        URL used to connect to RabbitMQ.
        """
        self._connection = None
        self._channel = None
        self._closing = False
        self._consumer_tag = None
        self._parameters = parameters
        self.queue = channel_name
        self.messages = []
        self.closing_event = threading.Event()

    def connect(self):
        """This method connects to RabbitMQ, returning the connection handle.
        When the connection is established, the on_connection_open method
        will be invoked by pika.

        :rtype: pika.SelectConnection

        """
        return pika.SelectConnection(self._parameters,
                                     self.on_connection_open,
                                     stop_ioloop_on_close=False)

    def on_connection_open(self, unused_connection):
        """This method is called by pika once the connection to RabbitMQ has
        been established. It passes the handle to the connection object in
        case we need it, but in this case, we'll just mark it unused.

        :type unused_connection: pika.SelectConnection

        """
        logging.info('Connection opened')
        self.add_on_connection_close_callback()
        self.open_channel()

    def add_on_connection_close_callback(self):
        """This method adds an on close callback that will be invoked by pika
        when RabbitMQ closes the connection to the publisher unexpectedly.

        """
        self._connection.add_on_close_callback(self.on_connection_closed)

    def on_connection_closed(self, connection, reply_code, reply_text):
        """This method is invoked by pika when the connection to RabbitMQ is
        closed unexpectedly. Since it is unexpected, we will reconnect to
        RabbitMQ if it disconnects.

        :param pika.connection.Connection connection: The closed connection obj
        :param int reply_code: The server provided reply_code if given
        :param str reply_text: The server provided reply_text if given

        """
        self._channel = None
        if self._closing:
            self._connection.ioloop.stop()
        else:
            logging.warning('Connection closed, reopening in 5 seconds: (%s) %s',
                           reply_code, reply_text)
            self._connection.add_timeout(5, self.reconnect)

    def reconnect(self):
        """Will be invoked by the IOLoop timer if the connection is
        closed. See the on_connection_closed method.

        """
        # This is the old connection IOLoop instance, stop its ioloop
        self._connection.ioloop.stop()

        if not self._closing:
            # Create a new connection
            self._connection = self.connect()

            # There is now a new connection, needs a new ioloop to run
            self._connection.ioloop.start()

    def open_channel(self):
        """Open a new channel with RabbitMQ by issuing the Channel.Open RPC
        command. When RabbitMQ responds that the channel is open, the
        on_channel_open callback will be invoked by pika.

        """
        logging.info('Creating a new channel')
        self._connection.channel(on_open_callback=self.on_channel_open)

    def on_channel_open(self, channel):
        """This method is invoked by pika when the channel has been opened.
        The channel object is passed in so we can make use of it.

        Since the channel is now open, we'll declare the exchange to use.

        :param pika.channel.Channel channel: The channel object

        """
        logging.info('Channel opened')
        self._channel = channel
        self._channel.basic_qos(prefetch_count=self.PREFETCH_COUNT)
        self.add_on_channel_close_callback()
        self.setup_exchange(self.EXCHANGE)

    def add_on_channel_close_callback(self):
        """This method tells pika to call the on_channel_closed method if
        RabbitMQ unexpectedly closes the channel.

        """
        self._channel.add_on_close_callback(self.on_channel_closed)

    def on_channel_closed(self, channel, reply_code, reply_text):
        """Invoked by pika when RabbitMQ unexpectedly closes the channel.
        Channels are usually closed if you attempt to do something that
        violates the protocol, such as re-declare an exchange or queue with
        different parameters. In this case, we'll close the connection
        to shutdown the object.

        :param pika.channel.Channel: The closed channel
        :param int reply_code: The numeric reason the channel was closed
        :param str reply_text: The text reason the channel was closed

        """
        logging.warning('Channel %i was closed: (%s) %s',
                       channel, reply_code, reply_text)
        self._connection.close()

    def setup_exchange(self, exchange_name):
        """Setup the exchange on RabbitMQ by invoking the Exchange.Declare RPC
        command. When it is complete, the on_exchange_declareok method will
        be invoked by pika.

        :param str|unicode exchange_name: The name of the exchange to declare

        """
        logging.info('Declaring exchange %s', exchange_name)
        self._channel.exchange_declare(self.on_exchange_declareok,
                                       exchange_name,
                                       self.EXCHANGE_TYPE)

    def on_exchange_declareok(self, unused_frame):
        """Invoked by pika when RabbitMQ has finished the Exchange.Declare RPC
        command.

        :param pika.Frame.Method unused_frame: Exchange.DeclareOk response frame

        """
        logging.info('Exchange declared')
        self.setup_queue(self.queue)

    def setup_queue(self, queue_name):
        """Setup the queue on RabbitMQ by invoking the Queue.Declare RPC
        command. When it is complete, the on_queue_declareok method will
        be invoked by pika.

        :param str|unicode queue_name: The name of the queue to declare.

        """
        logging.info('Declaring queue %s', queue_name)
        self._channel.queue_declare(self.on_queue_declareok, queue_name)

    def on_queue_declareok(self, method_frame):
        """Method invoked by pika when the Queue.Declare RPC call made in
        setup_queue has completed. In this method we will bind the queue
        and exchange together with the routing key by issuing the Queue.Bind
        RPC command. When this command is complete, the on_bindok method will
        be invoked by pika.

        :param pika.frame.Method method_frame: The Queue.DeclareOk frame

        """
        self._channel.queue_bind(self.on_bindok, self.queue,
                                 self.EXCHANGE, self.ROUTING_KEY)

    def on_bindok(self, unused_frame):
        """Invoked by pika when the Queue.Bind method has completed. At this
        point we will start consuming messages by calling start_consuming
        which will invoke the needed RPC commands to start the process.

        :param pika.frame.Method unused_frame: The Queue.BindOk response frame

        """
        logging.info('Queue bound')
        self.start_consuming()

    def start_consuming(self):
        """This method sets up the consumer by first calling
        add_on_cancel_callback so that the object is notified if RabbitMQ
        cancels the consumer. It then issues the Basic.Consume RPC command
        which returns the consumer tag that is used to uniquely identify the
        consumer with RabbitMQ. We keep the value to use it when we want to
        cancel consuming. The on_message method is passed in as a callback pika
        will invoke when a message is fully received.

        """
        logging.info('Issuing consumer related RPC commands')
        self.add_on_cancel_callback()
        self._consumer_tag = self._channel.basic_consume(self.on_message,
                                                         self.queue
                                                         )

    def add_on_cancel_callback(self):
        """Add a callback that will be invoked if RabbitMQ cancels the consumer
        for some reason. If RabbitMQ does cancel the consumer,
        on_consumer_cancelled will be invoked by pika.

        """
        self._channel.add_on_cancel_callback(self.on_consumer_cancelled)

    def on_consumer_cancelled(self, method_frame):
        """Invoked by pika when RabbitMQ sends a Basic.Cancel for a consumer
        receiving messages.

        :param pika.frame.Method method_frame: The Basic.Cancel frame

        """
        logging.info('Consumer was cancelled remotely, shutting down: %r',
                    method_frame)
        if self._channel:
            self._channel.close()

    def on_message(self, unused_channel, basic_deliver, properties, body):
        """Invoked by pika when a message is delivered from RabbitMQ. The
        channel is passed for your convenience. The basic_deliver object that
        is passed in carries the exchange, routing key, delivery tag and
        a redelivered flag for the message. The properties passed in is an
        instance of BasicProperties with the message properties and the body
        is the message that was sent.

        :param pika.channel.Channel unused_channel: The channel object
        :param pika.Spec.Basic.Deliver: basic_deliver method
        :param pika.Spec.BasicProperties: properties
        :param str|unicode body: The message body

        """

        self.messages.append((basic_deliver, body))

    def index_messages(self):
        """
        Both write tweets to json.gzip files and index them in Elasticsearch
        """
        retry_number = 0
        retry_factor = 0.1
        while True:
            if self._closing:
                break
            if len(self.messages) > FILEBREAK:
                retry_number = 0
                with LOCK:
                    tweets_batch = [json.loads(m[1].decode(encoding='UTF-8')) for m in self.messages]
                    last_id = self.messages[-1][0].delivery_tag
                    self.messages = []
                write_tweets(tweets_batch)
                res = True
                try:
                    res = es_index.storeTweetsWithTag(tweets_batch, datetime.now().strftime("%Y-%m-%d"))
                except Exception as error:
                    logging.error(error)
                    res = False

                if res:
                    self.acknowledge_message(last_id)
                else:
                    logging.error("unacknowledge " + str(len(tweets_batch)) + " tweets")
                    self.unacknowledge_message(last_id)
            else:
                sleeping_time = min((retry_factor * (2 ** retry_number)), 5)
                logging.info("sleeping {} seconds".format(sleeping_time))
                time.sleep(sleeping_time)
                retry_number += 1

    def acknowledge_message(self, delivery_tag):
        """Acknowledge the message delivery from RabbitMQ by sending a
        Basic.Ack RPC method for the delivery tag.

        :param int delivery_tag: The delivery tag from the Basic.Deliver frame

        """
        self._channel.basic_ack(delivery_tag, multiple=True)
        if self._closing:
            self.closing_event.set()

    def unacknowledge_message(self, delivery_tag):
        """Put message back in queue
        :param int delivery_tag: The delivery tag from the Basic.Deliver frame

        """
        self._channel.basic_nack(delivery_tag, multiple=True)
        if self._closing:
            self.closing_event.set()

    def stop_consuming(self):
        """Tell RabbitMQ that you would like to stop consuming by sending the
        Basic.Cancel RPC command.

        """
        if self._channel:
            logging.info('Sending a Basic.Cancel RPC command to RabbitMQ')
            self._channel.basic_cancel(self.on_cancelok, self._consumer_tag)

    def on_cancelok(self, unused_frame):
        """This method is invoked by pika when RabbitMQ acknowledges the
        cancellation of a consumer. At this point we will close the channel.
        This will invoke the on_channel_closed method once the channel has been
        closed, which will in-turn close the connection.

        :param pika.frame.Method unused_frame: The Basic.CancelOk frame

        """
        logging.info('RabbitMQ acknowledged the cancellation of the consumer')
        self.close_channel()

    def close_channel(self):
        """Call to close the channel with RabbitMQ cleanly by issuing the
        Channel.Close RPC command.

        """
        logging.info('Closing the channel')
        self._channel.close()

    def run(self):
        """Run the example consumer by connecting to RabbitMQ and then
        starting the IOLoop to block and allow the SelectConnection to operate.

        """
        self._connection = self.connect()
        self._connection.ioloop.start()

    def stop(self):
        """Cleanly shutdown the connection to RabbitMQ by stopping the consumer
        with RabbitMQ. When RabbitMQ confirms the cancellation, on_cancelok
        will be invoked by pika, which will then closing the channel and
        connection. The IOLoop is started again because this method is invoked
        when CTRL-C is pressed raising a KeyboardInterrupt exception. This
        exception stops the IOLoop which needs to be running for pika to
        communicate with RabbitMQ. All of the commands issued prior to starting
        the IOLoop will be buffered but not processed.

        """
        logging.info('Stopping')
        self._closing = True
        self.closing_event.wait(timeout=4)
        self.stop_consuming()
        self._connection.ioloop.start()
        logging.info('Stopped')

    def close_connection(self):
        """This method closes the connection to RabbitMQ."""
        logging.info('Closing connection')
        self._connection.close()

def get_file_name():
    """
    create directory tree structure depending on current date/time
    :return: str filename: path where the tweet file will be written
    """
    now = time.gmtime()
    time_tree = ["%Y", "%m", "%d", "%H", "%M"]
    for i in range(len(time_tree)):
        path = "/".join([time.strftime(time_tree[j], now) for j in range(i + 1)])
        path = "/tweets/" + path[:15] + "/"
        if not os.path.exists(args.path + path):
            os.makedirs(args.path + path)
    filename = args.path + path + time.strftime("%Y-%m-%dT%H_%M_%S", now) + "_" + container + ".json.gz"
    return filename


def write_tweets(tweets):
    """ write tweets to json.gz files, with a timestamp to archive collection date
    :param list tweets: list of tweets
    """
    with gzip.open(get_file_name(), 'ab') as outputfile:
        for data in tweets:
            obj = [round(time.time())]
            if ("id" in data):
                obj.append(data["id"])
            else:
                obj.append("-1")
            obj.append(data)
            json_str = json.dumps(obj) + "\n"
            json_bytes = json_str.encode('utf-8')
            outputfile.write(json_bytes)


def main():
    store_thread.start()
    try:
        consumer.run()
    except KeyboardInterrupt:
        consumer.stop()
        store_thread.join()


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--path', required=False, default="/usr/src/app/data/", help='Path to tweets storage folder')
    parser.add_argument('--es_host', required=False, default="elastic-master", help='Host of elasticsearch database')
    parser.add_argument('--es_port', required=False, default=9200, help='Port of elasticsearch database')
    parser.add_argument('--es_index', required=False, default='tweets-index', help='Elasticsearch index name')
    parser.add_argument('--rabbit_host', required=False, default="rabbitmq", help='RabbitMQ host')
    parser.add_argument('--rabbit_port', required=False, default=5672, help='RabbitMQ port')
    parser.add_argument('--rabbit_channel', required=False, default='tweets', help='RabbitMQ channel name')
    # parser.add_argument('--filebreak', required=False, type=int, default=1000,
    #                     help='Number of lines each file should contain')
    args = parser.parse_args()
    logging.basicConfig(format='%(asctime)s - %(levelname)s : %(message)s', level=logging.INFO)
    es_index = TweetsIndex(args.es_host, args.es_port, args.es_index)
    container = socket.gethostname()
    parameters = pika.ConnectionParameters(host=args.rabbit_host, port=args.rabbit_port,
                                           connection_attempts=100, retry_delay=1,
                                           # blocked_connection_timeout=1000,
                                           # socket_timeout=1000,
                                           ssl=False,
                                           credentials=pika.credentials.PlainCredentials(
                                               username='user',
                                               password='password'))
    consumer = Consumer(args.rabbit_channel, parameters)
    store_thread = threading.Thread(target=consumer.index_messages)
    main()
