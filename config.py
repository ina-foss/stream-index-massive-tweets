# OAuth authentication keys to Twitter API
ACCESS = [
    (
        "copy here key 0 oauth.consumerKey",
        "copy here key 0 oauth.consumerSecret",
        "copy here key 0 oauth.accessToken",
        "copy here key 0 oauth.accessTokenSecret"
    ),
    (
        "copy here key 1 oauth.consumerKey",
        "copy here key 1 oauth.consumerSecret",
        "copy here key 1 oauth.accessToken",
        "copy here key 1 oauth.accessTokenSecret"
    ),
    (
        "copy here key 2 oauth.consumerKey",
        "copy here key 2 oauth.consumerSecret",
        "copy here key 2 oauth.accessToken",
        "copy here key 2 oauth.accessTokenSecret"
    ),
    (
        "copy here key 3 oauth.consumerKey",
        "copy here key 3 oauth.consumerSecret",
        "copy here key 3 oauth.accessToken",
        "copy here key 3 oauth.accessTokenSecret"
    )
]

# keywords to be tracked using the Twitter filter API and tags to indicate the collection method within the tweet body
# there should be maximum len(ACCESS)-1 collection methods (the first key in ACCESS is dedicated to Twitter sample API)
KEYWORDS = [
    {"tag": "pronouns", "track": ["je", "tu"]},
    {"tag": "adverbs", "track": ["hier", "toujours", "beaucoup"]},
    {"tag": "verbs", "track": ["etre", "avoir", "faire"]}
]

# language to be tracked using the Twitter filter API.
LANG = "fr"

# approximate file size
FILEBREAK = 300


PROXY = {}

