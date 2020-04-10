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
    )
]

# track: keywords to be tracked using the Twitter filter API
# tag: string added to the tweet body before indexation to indicate the collection method
KEYWORDS = [
    {"tag": "my_tag", "track": "je tu il elle nous"},
]

# language to be tracked using the Twitter filter API.
LANG = "fr"

# approximate file size
FILEBREAK = 300

# example PROXY = {'http': 'http://my_proxy:port', 'https': 'https://my_proxy:port'}
PROXY = {}

