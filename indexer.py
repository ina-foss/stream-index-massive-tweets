from elasticsearch import Elasticsearch, helpers, exceptions
from datetime import datetime, date, timedelta
import logging
from clean_url import clean_url
import json
import socket
import time
DATE_FORMAT = "%Y-%m-%dT%H:%M:%S"
TWITTER_DATE_FORMAT = "%a %b %d %H:%M:%S +0000 %Y"

class TweetsIndex:

    def __init__(self, host, port, prefix, day=""):
        self.es = Elasticsearch([("%s:%s" % (host,port))])
        self.pre = prefix
        self.day = day

    def create_index(self, index_name):
        with open("mapping.json") as f:
            settings = json.load(f)
        logging.info("Creating index: " + index_name + ", settings: " + str(settings["settings"]))
        for retry in range(3):
            try:
                res = self.es.indices.create(index=index_name, body=settings)
                if res["acknowledged"]:
                    return
            except socket.timeout:
                logging.error("Timeout error, check if index was created")
                time.sleep(10)
                if self.es.indices.exists(index_name):
                    return
        raise ConnectionError("Index " + index_name + " cannot be created")

    def open_indices(self, day):
        weeks = [self.pre + "-" + str(week[0]) + "-" + str(week[1]) for week in self.get_weeks(day)]
        for week in weeks:
            try:
                status = self.es.cat.indices(week, format="json")[0]["status"]
            except exceptions.NotFoundError:
                self.create_index(week)
                time.sleep(10)
                status = self.es.cat.indices(week, format="json")[0]["status"]
            if status != "open":
                self.es.indices.open(index=week)
        opened_indices = self.es.indices.get(self.pre + "*")
        for key in opened_indices:
            if key not in weeks and "do_not_close" not in opened_indices[key]["aliases"]:
                self.es.indices.close(index=key)

    def get_weeks(self, day):
        day = date(int(day[:4]), int(day[5:7]), int(day[8:]))
        first_day = day - timedelta(days=8)
        last_day = day + timedelta(days=1)
        delta = last_day - first_day
        weeks = set()
        for i in range(delta.days + 1):
            week = (first_day + timedelta(days=i)).isocalendar()
            if week[1] not in weeks:
                weeks.add(week[1])
                yield week

    def create_update_list(self, tweets):
        to_update = []
        for tweet in tweets:
            if "id" in tweet:
                week = datetime.strptime(tweet["created_at"], TWITTER_DATE_FORMAT).isocalendar()
                try:
                    format = {
                        '_op_type': 'update',
                        '_type': 'tweets',
                        '_index': self.pre + "-" + str(week[0]) + "-" + str(week[1]),
                        '_id': tweet["id"],
                        'script': {
                            'lang': 'painless',
                            'inline': ("ctx._source.tags.add(params.query) ;\
                               ctx._source.retweet_count = params.retweet_count ; \
                               ctx._source.quote_count = params.quote_count ; \
                               ctx._source.reply_count = params.reply_count ; \
                               ctx._source.favorite_count = params.favorite_count"),
                            "params": {
                                "query": tweet["tags"][0],
                                "retweet_count": tweet["retweet_count"],
                                "quote_count": tweet["quote_count"],
                                "reply_count": tweet["reply_count"],
                                "favorite_count": tweet["favorite_count"]
                            }
                        },
                        'upsert': tweet
                    }
                    to_update.append(format)
                except Exception as error:
                    logging.error(tweet)
                    logging.error(error)
        return to_update

    def hashtags_format(self, tweet, entities):
        hashtags = entities["hashtags"]
        tweet["hashtags_list"] = sorted([hashtag["text"] for hashtag in hashtags])
        tweet["hashtags"] = " ".join(tweet["hashtags_list"])
        return tweet

    def standard_format(self, tweet):
        if "extended_tweet" in tweet:
            if "full_text" in tweet["extended_tweet"]:
                tweet["text"] = tweet["extended_tweet"]["full_text"]
                tweet["extended_tweet"].pop("full_text")
            if "entities" in tweet["extended_tweet"]:
                if "hashtags" in tweet["extended_tweet"]["entities"] \
                        and tweet["extended_tweet"]["entities"]["hashtags"] != []:
                    tweet = self.hashtags_format(tweet, tweet["extended_tweet"]["entities"])
                    tweet["extended_tweet"]["entities"].pop("hashtags")
                if "urls" in tweet["extended_tweet"]["entities"]:
                    for url in tweet["extended_tweet"]["entities"]["urls"]:
                        url["clean_url"] = clean_url(url["expanded_url"])
                        for key in ["display_url", "url", "indices"]:
                            url.pop(key, None)
                        tweet["entities"]["urls"].append(url)
                    tweet["extended_tweet"]["entities"].pop("urls")
                if "user_mentions" in tweet["extended_tweet"]["entities"]:
                    for mention in tweet["extended_tweet"]["entities"]["user_mentions"]:
                        tweet["entities"]["user_mentions"].append(mention)
                    tweet["extended_tweet"]["entities"].pop("user_mentions")
            if "extended_entities" in tweet["extended_tweet"] \
                    and "media" in tweet["extended_tweet"]["extended_entities"]:
                # keep all media information in tweet["extended_entities"]["media"]. All other fields are deleted.
                tweet["extended_entities"] = {}
                tweet["extended_entities"]["media"] = tweet["extended_tweet"]["extended_entities"]["media"]
                tweet["extended_tweet"].pop("extended_entities")
                tweet["extended_tweet"]["entities"].pop("media")

        else:
            if "entities" in tweet:
                if "hashtags" in tweet["entities"] and tweet["entities"]["hashtags"] != []:
                    tweet = self.hashtags_format(tweet, tweet["entities"])
                    tweet["entities"].pop("hashtags")
            if "extended_entities" in tweet and "media" in tweet["extended_entities"]:
                # keep all media information in tweet["extended_entities"]["media"]. All other fields are deleted.
                tweet["entities"].pop("media")
        for key in tweet["user"].copy():
            if "profile" in key:
                tweet["user"].pop(key)
        tweet["links"] = []
        for url in tweet["entities"]["urls"]:
            url["clean_url"] = clean_url(url["expanded_url"])
            for key in ["display_url", "url", "indices"]:
                url.pop(key, None)
            if not url["clean_url"].startswith('https://twitter.com/'):
                tweet["links"].append(url["clean_url"])
        tweet["indexing_date"] = datetime.now().strftime(DATE_FORMAT)
        return tweet

    def subtweet_format(self, tweet, type):
        subtweet = self.standard_format(tweet[type])
        tweet[type + "_user_screen_name"] = subtweet["user"]["screen_name"]
        tweet[type + "_user_id_str"] = subtweet["user"]["id_str"]
        tweet[type + "_id_str"] = subtweet["id_str"]
        if "extended_entities" in subtweet and "media" in subtweet["extended_entities"]:
            tweet[type + "_media"] = subtweet["extended_entities"]["media"]
        if "entities" in subtweet and "urls" in subtweet["entities"]:
            tweet[type + "_urls"] = subtweet["entities"]["urls"]
            for url in subtweet["entities"]["urls"]:
                if not url["clean_url"].startswith('https://twitter.com/'):
                    tweet["links"].append(url["clean_url"])
            tweet["links"] = list(set(tweet["links"]))
        tweet[type + "_text"] = subtweet["text"]

        if "quote_count" not in subtweet:
            subtweet["quote_count"] = None
        if "reply_count" not in subtweet:
            subtweet["reply_count"] = None
        subtweet["is_retweet"] = False
        return tweet

    def format_tweets(self, tweets, day):
        day = datetime.strptime(day, "%Y-%m-%d")
        retweets_and_quotes = []
        quotes_from_retweets = []
        tweets_set = set()
        formatted_tweets = []
        for tweet in tweets:
            if "id" in tweet:
                # if (tweet["id"], tweet["tags"][0]) in tweets_set:
                if tweet["id"] in tweets_set:
                    continue
                if (day - datetime.strptime(tweet["created_at"], TWITTER_DATE_FORMAT)).days > 7:
                    continue
                # tweets_set.add((tweet["id"], tweet["tags"][0]))
                tweets_set.add(tweet["id"])
                tweet = self.standard_format(tweet)

                if "retweeted_status" in tweet:
                    tweet["is_retweet"] = True
                    tweet["text"] = tweet["retweeted_status"]["text"]
                    date_created = datetime.strptime(tweet["retweeted_status"]["created_at"], TWITTER_DATE_FORMAT)
                    if (day - date_created).days <= 7:
                        tweet["retweeted_status"]["tags"] = ["from_retweet"]
                        retweets_and_quotes.append(tweet["retweeted_status"])
                    tweet = self.subtweet_format(tweet, "retweeted_status")
                    tweet.pop("retweeted_status")
                else:
                    tweet["is_retweet"] = False

                if "quoted_status" in tweet:
                    date_created = datetime.strptime(tweet["quoted_status"]["created_at"], TWITTER_DATE_FORMAT)
                    if (day - date_created).days <= 7:
                        tweet["quoted_status"]["tags"] = ["from_quote"]
                        retweets_and_quotes.append(tweet["quoted_status"])
                    tweet = self.subtweet_format(tweet, "quoted_status")
                    tweet.pop("quoted_status")
                tweet["len"] = len(tweet["text"])
                formatted_tweets.append(tweet)

        for tweet in retweets_and_quotes:
            # if (tweet["id"], tweet["tags"][0]) in tweets_set:
            if tweet["id"] in tweets_set:
                continue
            # tweets_set.add((tweet["id"], tweet["tags"][0]))
            tweets_set.add(tweet["id"])
            if "quoted_status" in tweet:
                date_created = datetime.strptime(tweet["quoted_status"]["created_at"], TWITTER_DATE_FORMAT)
                if (day - date_created).days <= 7:
                    tweet["quoted_status"]["tags"] = ["from_quote"]
                    quotes_from_retweets.append(tweet["quoted_status"])
                tweet = self.subtweet_format(tweet, "quoted_status")
                tweet.pop("quoted_status")
            tweet["len"] = len(tweet["text"])
            formatted_tweets.append(tweet)

        for tweet in quotes_from_retweets:
            # if (tweet["id"], tweet["tags"][0]) in tweets_set:
            if tweet["id"] in tweets_set:
                continue
            if (day - datetime.strptime(tweet["created_at"], TWITTER_DATE_FORMAT)).days > 7:
                continue
            # tweets_set.add((tweet["id"], tweet["tags"][0]))
            tweets_set.add(tweet["id"])
            tweet["len"] = len(tweet["text"])
            formatted_tweets.append(tweet)

        return formatted_tweets

    def storeTweetsWithTag(self, tweets, day, chunk_size=3200):
        if day != self.day:
            self.open_indices(day)
            self.day = day
        tweets = self.format_tweets(tweets, day)
        to_update = self.create_update_list(tweets)
        helpers.bulk(self.es, to_update, chunk_size=chunk_size, request_timeout=20)
        return True
