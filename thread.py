import threading

from streamer import *
from config import ACCESS

e = threading.Event()


class StreamThread(threading.Thread):
    def __init__(self, key, rabbit_host, rabbit_port, **request):
        """Create a new Thread instance. Its run method will start streamer.
        :param int key: identifier of the Twitter OAuth authentication key. Corresponds to
        an index in the config.ACCESS list
        :param dict request: instructions to streamer. request["track"]: a list of keywords tracked by the filter API ;
        request["tag"]: a string that will be added to the tweet body to indicate its collection method
        """
        threading.Thread.__init__(self)
        self.key = key
        self.lang = request["lang"] if "lang" in request else None
        self.track = request["track"] if "track" in request else None
        if "tag" not in request:
            if "track" not in request:
                self.tag = "_sample" + "_" + str(self.lang)
            else:
                self.tag = "_filter_" + "-".join(request["track"]) + "_" + str(self.lang)
        else:
            self.tag = request["tag"]
        self.twitter = sampleStreamer(rabbit_host, rabbit_port, *ACCESS[self.key], self.tag)

    def run(self):
        """start streamer
        """
        if self.track is None:
            self.twitter.sample(self.lang)
        else:
            self.twitter.filter(self.track, self.lang)
        e.set()


if __name__ == "__main__":
    s = StreamThread(0, "rabbitmq", 5672)
    s.start()
    input("Press Enter to end streaming. \n")
    s.twitter.do_continue = False
    s.join()
